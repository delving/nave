"""
This module contains all the functionality to store, retrieve webresource.

In addition it will also be able to:

    * create deepzoom and thumbnails derivatives
    * extract color from the source image
    * detect mime-type
    * store relevant meta-information into a json serializable companion file
    * detect out of sync masters and derivatives and create new derivatives on
    the fly

"""
import mimetypes
import shutil
import urllib
from datetime import timedelta
from glob import glob
import hashlib
import json
import logging
import os
import re
import subprocess
from urllib.error import HTTPError

import magic
import time
from colorific.palette import extract_colors
from PIL import Image
import requests
import webcolors
from django.conf import settings

logger = logging.getLogger(__file__)

SOURCE_DIR = "source"
CACHE_DIR = "cache"
THUMBNAIL_DIR = "derivatives/thumbnails"
DEEPZOOM_DIR = "derivatives/deepzoom"
RDF_DIR = "rdf"
NARTHEX_DIR = "narthex"

WEB_RESOURCE_DIRS = [
    SOURCE_DIR,
    CACHE_DIR,
    THUMBNAIL_DIR,
    DEEPZOOM_DIR,
    RDF_DIR,
    NARTHEX_DIR
]

SUPPORTED_IMAGE_EXTENSIONS = [
    "jpg",
    "jpeg",
    "jp2",
    "tif",
    "tiff",
    "png",
]


class WebResource:

    def __init__(self, spec, uri=None, path=None, hub_id=None, base_dir=None, settings=None, org_id=None,
                 domain=None):
        self.spec = spec
        self._uri = uri
        self._source_path = path
        self._hub_id = hub_id
        self._base_dir = base_dir
        self._settings = settings
        self._org_id = org_id
        self._domain = domain
        self._json = None
        self._mime_type = None
        self.create_dataset_webresource_dirs()

    @property
    def base_dir(self):
        if not self._base_dir:
            self._base_dir = self.settings.WEB_RESOURCE_BASE
        if not self._base_dir.rstrip('/').endswith("/webresource"):
            self._base_dir = "{}/webresource".format(self._base_dir.rstrip('/'))
        return self._base_dir

    @property
    def domain(self):
        if not self._domain:
            self._domain = self.settings.RDF_BASE_URL
        if "://" not in self._domain:
            self._domain = "http://{}".format(self._domain)
        return self._domain

    @property
    def settings(self):
        if not self._settings:
            from django.conf import settings
            self._settings = settings
        return self._settings

    @property
    def org_id(self):
        if not self._org_id:
            self._org_id = self.settings.ORG_ID
        return self._org_id

    @property
    def hub_id(self):
        """Return the hub_id of the RDF record linked to the WebResource."""
        if not self._hub_id:
            self.from_json()
            if 'hub_id' in self._json:
                self._hub_id = self._json.get('hub_id')
        return self._hub_id

    @property
    def has_linked_hub_id(self):
        """Is the WebResource linked to a EDM Record via an hub_id."""
        return self.hub_id is not None

    @property
    def get_spec_dir(self):
        """Return the basepath to the WebResource spec dir."""
        return os.path.join(self.base_dir, self.get_relative_spec_dir)

    @property
    def get_relative_spec_dir(self):
        """Return the relative path to the WebResource spec dir."""
        return os.path.join(self.org_id, self.spec)

    @property
    def exist_webresource_dirs(self):
        return all(os.path.exists(os.path.join(self.get_spec_dir, p)) for p in WEB_RESOURCE_DIRS)

    @property
    def exists_deepzoom(self):
        """Check if the deepzoom derivative already exists."""
        return os.path.exists(self.get_deepzoom_path)

    @property
    def exists_source(self):
        """Check in the source of the WebResource exists."""
        return os.path.exists(self.uri_to_path)

    def exists_thumbnail(self, width, height):
        """Check if the thumbnail derivative already exists."""
        return os.path.exists(self.get_thumbnail_path(width=width, height=height))

    def create_dataset_webresource_dirs(self):
        """Create all subdirectories for the WebResource based on spec."""
        if not self.exist_webresource_dirs:
            for folder in WEB_RESOURCE_DIRS:
                full_path = os.path.join(self.get_spec_dir, folder)
                os.makedirs(full_path, exist_ok=True, mode=0o777)
            return True
        return False

    def create_deepzoom(self):
        """Create an IIPimage server compliant tiled deepzoom pyramid tiff.

        If force is true a new item is created each time otherwise it will skip.

        # vips im_vips2tiff source_image output_image.tif:deflate,tile:256x256,pyramid

        """
        start = time.time()
        input_file = self.get_source_path
        output_file = self.get_deepzoom_path
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        created = subprocess.check_call(
            ["vips", "im_vips2tiff", input_file] +
            ["{}:deflate,tile:256x256,pyramid".format(output_file)])
        elapsed = (time.time() - start)
        logger.info("Deepzoomed {} => {} in {}".format(input_file, output_file, str(timedelta(seconds=elapsed))))
        return True if created == 0 else False

    def create_thumbnail(self, width, height):
        """Create the thumbnail derivative of the source digital object."""
        max_size = getattr(settings, 'WEB_RESOURCE_MAX_SIZE', 1000)
        if not isinstance(max_size, int):
            max_size = int(max_size)
        if width > max_size or height > max_size:
            width = height = max_size
        start = time.time()
        infile = self.get_source_path
        outfile = self.get_thumbnail_path(width, height)
        try:
            os.makedirs(os.path.dirname(outfile), exist_ok=True)
            im = Image.open(infile)
            im.thumbnail((width, height))
            im.save(outfile, "JPEG")
            elapsed = (time.time() - start)
            logger.info("Thumbnailed {} => {} in {}".format(infile, outfile, str(timedelta(seconds=elapsed))))
        except IOError as err:
            logger.error("cannot create thumbnail for {} because of {}".format(infile, err))
            return False
        return True

    def get_all_derivatives(self):
        """Get all derivatives and return the paths as a list."""
        # todo: implement this as a glob
        path = os.path.join(self.get_spec_dir, self.get_derivative_base_path(THUMBNAIL_DIR))
        derivatives = glob("{}_*".format(path))
        derivatives.append(self.get_deepzoom_path)
        return derivatives

    def remove_all_derivatives(self):
        """Remove all derivatives of the source digital object."""
        for path in self.get_all_derivatives():
            if os.path.exists(path):
                os.remove(path)
        logger.info("Deleted all derivatives for {}".format(self.uri))

    def is_derivative_stale(self, derivative_path):
        """Determine if source is modified after the derivative is created.

        When the source has been modified after the derivative is created it,
        all derivatives should be cleared and on access recreated.
        """
        if not self.exists_source:
            return False
        source_path = self.get_source_path
        return os.path.exists(derivative_path) and os.path.getmtime(derivative_path) < os.path.getmtime(source_path)

    @staticmethod
    def get_hash(uri):
        """Create SHA256 hash from a URI.
        :param uri: The
        """
        return hashlib.sha256(uri.encode("utf-8")).hexdigest()

    @property
    def is_cached(self):
        """Is the WebResource cached from the web or source original on disk."""
        return not self.uri.startswith('urn:')

    @property
    def is_image(self):
        """Determine in source digital object is an image."""
        path, ext = os.path.splitext(self.get_source_path)
        return ext.lower() in SUPPORTED_IMAGE_EXTENSIONS

    @property
    def uri(self):
        """The uri of the object.

        This is either the URN or the full external URL of the digital object.
        """
        if not self._uri and self._source_path:
            self._uri = self.path_to_uri
        elif not self._uri and not self._path:
            raise ValueError("Either path or uri must be given in the constructor")
        return self._uri

    @property
    def clean_uri(self):
        """Remove the URN prefix and the spec from the source URI.

        The cached uri should be returned without any changes.
        """
        return self.uri.replace("urn:{}/".format(self.spec), "") if not self.is_cached else self.uri

    def get_cache_uri(path):
        """Get the Cache Source URI from the metadata.

        This is the external URL where the digital object is cached from.
        """
        raise NotImplementedError("implement me")

    @property
    def path_to_uri(self):
        """
        Reconstruct the uri from the source path.

        This will work both for cached and source paths.
        """
        path = self._source_path
        base, rel_path = path.split('/{}/'.format(self.spec, max_split=1))
        if rel_path.startswith(SOURCE_DIR):
            uri = rel_path.replace("{}/".format(SOURCE_DIR), "urn:{}/".format(self.spec))
        elif rel_path.startswith(CACHE_DIR):
            uri = self.get_cache_uri()
        else:
            mesg = "Path {} not found in WebResource store for spec {}".format(path, self.spec)
            logger.warn(mesg)
            raise ValueError(mesg)
        return uri

    @property
    def uri_to_path(self):
        """Given the URI give back the path to the WebResource source object."""
        path = None
        if self.is_cached:
            path = os.path.join(self.get_spec_dir,
                                self.get_derivative_base_path(kind=CACHE_DIR))
        else:
            path = os.path.join(self.get_spec_dir, SOURCE_DIR, self.clean_uri)
        webresource_path = self.get_from_source_path(path)
        if webresource_path and not self._source_path:
            self._source_path = webresource_path
        return webresource_path

    def get_derivative_base_path(self, uri=None, kind=THUMBNAIL_DIR):
        """Create base path for the derivatives.

        Note: that this does not include the size or mime-type extensions
        """
        if not uri:
            uri = self.uri
        sha = self.get_hash(uri)
        sub_dirs = re.findall('...?', sha)[:3]
        sub_dirs.insert(0, kind)
        sub_dirs.append(sha)
        return os.path.join(*sub_dirs)

    @property
    def get_deepzoom_path(self):
        """Get the fully qualified path to the Deepzoom Tile."""
        return os.path.join(
            self.get_spec_dir,
            "{}.tif".format(self.get_derivative_base_path(kind=DEEPZOOM_DIR)),
        )

    NON_DEFAULT_EXTENSIONS = {
        "jpeg": "jpg",
        "tiff": "tif"
    }

    def sort_extensions(self, wr_list):
        """Sort a list of webresources by extension."""
        from collections import defaultdict
        wr_dict = defaultdict(list)
        for wr in sorted(wr_list):
            path, ext = os.path.splitext(wr)
            clean_ext = ext.lower().lstrip('.')
            if clean_ext in self.NON_DEFAULT_EXTENSIONS:
                clean_ext = self.NON_DEFAULT_EXTENSIONS[clean_ext]
            wr_dict[clean_ext].append(wr)
        return wr_dict

    def get_source_path_matches(self, webresource_path):
        """Return all matches to the w"""
        # strip extension
        path = os.path.splitext(webresource_path)[0]
        # find the path
        full_path = os.path.join(self, path)
        return glob("{}*".format(full_path))

    def get_from_source_path(self, webresource_path):
        matches = self.get_source_path_matches(webresource_path)
        if len(matches) > 1:
            wr_dict = self.sort_extensions(matches)
            for ext in ['tif', 'jp2', 'jpg']:
                if ext in wr_dict:
                    return wr_dict[ext][0]
        elif len(matches) == 1:
            return matches[0]
        return None

    @property
    def get_source_path(self):
        """Get the fully qualified path to the source digital object."""
        if not self._source_path:
            return self.uri_to_path
        return self._source_path

    def get_thumbnail_path(self, width, height):
        """Get the fully qualified path to the thumbnail."""
        return os.path.join(
            self.get_spec_dir,
            "{}_{}x{}.jpg".format(
                self.get_derivative_base_path(kind=THUMBNAIL_DIR),
                width,
                height
            )
        )

    @property
    def get_deepzoom_uri(self):
        """Get fully qualified deepzoom URI for redirection to the WebServer."""
        # todo remove later when nginx works properly
        return "{}/fcgi-bin/iipsrv.fcgi?DeepZoom={}/{}/{}.tif.dzi".format(
            self.domain,
            settings.WEB_RESOURCE_BASE.rstrip('/'),
            self.get_relative_spec_dir,
            self.get_derivative_base_path(kind=DEEPZOOM_DIR))
        # return os.path.join(
        #     self.domain,
        #     "webresource",
        #     self.get_relative_spec_dir,
        #     "{}.tif.dzi".format(self.get_derivative_base_path(kind=DEEPZOOM_DIR))
        # )

    @property
    def get_source_uri(self):
        """Get the fully qualified path to the source digital object."""
        return os.path.join(
            self.domain,
            "webresource",
            self.get_relative_spec_dir,
            self.clean_uri
        )

    def get_thumbnail_uri(self, width, height, mime_type="jpeg"):
        """Get fully qualified thumbnail URI for redirection to the WebServer."""
        return os.path.join(
            self.domain,
            "webresource",
            self.get_relative_spec_dir,
            "{}_{}x{}.jpg".format(
                self.get_derivative_base_path(kind=THUMBNAIL_DIR),
                width,
                height,
            )
        )

    def get_deepzoom_redirect(self):
        """All processing steps for finding, creating, and redirecting to the deepzoom derivative."""
        if self.is_derivative_stale(self.get_deepzoom_path):
            self.remove_all_derivatives()
        if not self.exists_source and self.is_cached:
            self.cache_external_uri()
            if not self.exists_source:
                return None
        if not self.exists_deepzoom:
            created = self.create_deepzoom()
            if created:
                uri = self.get_deepzoom_uri
            else:
                uri = None
        else:
            uri = self.get_deepzoom_uri
        return uri

    def get_source_redirect(self):
        """Get the redirect URL to the source digital object for download.

        This is mostly used for document and other links. For Source images the access should be limited.
        """
        if self.exists_source:
            return self.get_source_uri
        return None

    def get_thumbnail_redirect(self, width, height):
        """All processing steps for finding, creating, and redirecting to the thumbnail derivative."""
        thumbnail_path = self.get_thumbnail_path(width, height)
        if self.is_derivative_stale(thumbnail_path):
            self.remove_all_derivatives()
        if not self.exists_source and self.is_cached:
            self.cache_external_uri()
            if not self.exists_source:
                return None
        if not self.exists_thumbnail(width, height):
            created = self.create_thumbnail(width, height)
            if created:
                uri = self.get_thumbnail_uri(width, height)
            else:
                uri = None
        else:
            uri = self.get_thumbnail_uri(width, height)
        return uri

    @property
    def color_palette(self):
        """Extract the colors and return the color palette."""
        return self._extract_colors()

    @property
    def get_colors(self):
        hex_colors = [webcolors.rgb_to_hex(c.value) for c in self.color_palette.colors]
        return hex_colors

    @property
    def get_background_color(self):
        return webcolors.rgb_to_hex(self.color_palette.bgcolor.value)

    def closest_colour(self, requested_colour):
        """
        requested_colour = (119, 172, 152)
        actual_name, closest_name = get_colour_name(requested_colour)
        """
        min_colours = {}
        for key, name in webcolors.css3_hex_to_names.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - requested_colour[0]) ** 2
            gd = (g_c - requested_colour[1]) ** 2
            bd = (b_c - requested_colour[2]) ** 2
            min_colours[(rd + gd + bd)] = name
        return min_colours[min(min_colours.keys())]

    def get_colour_name(self, requested_colour):
        try:
            closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
        except ValueError:
            closest_name = self.closest_colour(requested_colour)
            actual_name = None
        return actual_name, closest_name

    def _extract_colors(self):
        return extract_colors(self.get_source_path)

    @property
    def get_json_path(self):
        """Get the path to the json metadata file. """
        path, extension = os.path.splitext(self.get_source_path)
        return "{}.json".format(path)

    @property
    def exists_json(self):
        """Check if the json file is available on disk."""
        return os.path.exists(self.get_json_path)

    @property
    def is_source_deleted(self):
        """Check if the source is deleted but the json and derivatives remain."""
        return not self.exists_source and self.exists_json

    @property
    def get_all_webresource_files(self):
        """Return a list of paths of all the files linked to this webresource."""
        files = self.get_all_derivatives()
        files.append(self.get_deepzoom_path)
        files.append(self.get_json_path)
        return files

    @property
    def purge_webresource(self):
        """Delete all the files linked to this webresource.

        This is normally used when the source file has been deleted.
        """
        for path in self.get_all_webresource_files:
            os.remove(path)
        logger.info("Removed all linked files for {}".format(self.uri))

    def to_json(self):
        """Persist the generated WebResource information to disk.

        This json file is stored next to the source digital object with a .json extension.
        """
        # TODO: implement me
        # check if object exists and then upsert
        pass

    def from_json(self):
        """Retrieve the persisted WebResource information from disk."""
        metadata = json.load(self.get_json_path)
        if metadata:
            self._json = metadata
        return metadata

    def to_rdf(self, rdf_format="nt"):
        # TODO: implement me
        """Convert the WebResource to an EDM compliant RDF serialization."""
        pass

    def extract_object_number(self):
        """Extract the object number from the filename of the source object."""
        object_number = None
        if "__" in self.uri and not self.is_cached:
            object_number, fname = self.clean_uri.split("__", max_split=1)
        elif self.has_linked_hub_id:
            object_number = self.hub_id.split('_')[-1]
        return object_number

    def generate_edm_rdf_subject(self):
        """Reconstruct the EDM RDF subject from the available information in the WebResource.

        This link can be used to connect the webresource to the EDM record.
        """
        object_number = self.extract_object_number
        subject = None
        if object_number:
            subject = "{domain}/resource/aggregation/{spec}/{id}".format(
                self.domain,
                self.spec,
                object_number
            )
        return subject

    def generate_edm_rdf_graph(self):
        """Generate the EDM RDF graph that the WebResource is linked to."""
        subject = self.generate_edm_rdf_subject()
        graph_name = None
        if subject:
            graph_name = subject.rstrip('/') + "/graph"
        return graph_name

    def cache_remote_link(self, uri):
        """Retrieve remoted digital object and store it as cached object.

        HTML pages are not considered digital objects in this context.
        """
        response = requests.get(uri)
        if response.status == 200:
            pass
        # TODO: implement me

    def test_something(self):
        self.cache_remote_link()

    def guess_mime_type(self, path):
        """Guess the extension and mime-type of the file."""
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as m:
            mime_type = m.id_filename(path)
        extension = mimetypes.guess_extension(mime_type)
        return mime_type, extension

    def cache_external_uri(self):
        """Retrieve digital object from remote URI and store it in the spec cache directory."""
        if not self.is_cached:
            return
        try:
            logger.info("Attempting to cache: {}".format(self.uri))
            local_filename, headers = urllib.request.urlretrieve(self.uri)
            mime_type = headers.get('Content-Type')
            if not mime_type:
                mime_type, extension = self.guess_mime_type(local_filename)
            extension = mimetypes.guess_extension(mime_type)
            os.makedirs(os.path.dirname(self.get_source_path), exist_ok=True)
            shutil.move(local_filename, self.get_source_path)
        except HTTPError as he:
            logger.error(he.code, he.reason)

    @staticmethod
    def get_redirect_url(absolute_uri):
        """
        Retrieving the WebResource derivative URIs
        """
        from urllib.parse import urlparse, parse_qs
        parse_result = urlparse(absolute_uri)
        params = parse_qs(parse_result.query)

        uri = params.get('uri')
        hub_id = params.get('hubId')
        doc_type = params.get('docType', "thumbnail")
        width = params.get('width', None)
        height = params.get('height', None)
        spec = params.get('spec')

        if not spec or (not uri and not hub_id):
            raise ValueError("Missing required query parameters. 'spec' and 'uri' or 'hub_id' must be supplied")

        if not height and not width:
            width = height = 220
        elif width and not height:
            height = width
        elif height and not width:
            width = height

        if not isinstance(width, int):
            width = int(width)
        if not isinstance(height, int):
            height = int(height)

        domain = "{}://{}".format(parse_result.scheme, parse_result.net_loc)
        if settings.DEBUG:
            domain = domain.replace(':8000', '')

        # media_type = params.get('mediaType')
        # default_image = params.get('defaultImage')
        if not spec and hub_id:
            org_id, spec, local_id = hub_id.split('_')

        from .webresource import WebResource
        webresource = WebResource(uri=uri, hub_id=hub_id, spec=spec, domain=domain)
        redirect_uri = None
        if doc_type == 'thumbnail':
            redirect_uri = webresource.get_thumbnail_redirect(width, height)
        elif doc_type == "deepzoom":
            redirect_uri = webresource.get_deepzoom_redirect()
        # TODO: possibly later add route to source for logged in or APi token users
        return redirect_uri
