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
import hashlib
import logging
import os
import re

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


class WebResource:

    def __init__(self, spec, uri=None, path=None, base_dir=None, settings=None, org_id=None):
        self._uri = uri
        self._source_path = path
        self.spec = spec
        self._base_dir = base_dir
        self._settings = settings
        self._org_id = org_id

    @property
    def base_dir(self):
        if not self._base_dir:
            self._base_dir = self.settings.WEB_RESOURCE_BASE
        return self._base_dir

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
    def get_spec_dir(self):
        """Return the basepath to the WebResource spec dir."""
        return os.path.join(self.base_dir, self.org_id, self.spec)

    @property
    def exist_webresource_dirs(self):
        return all(os.path.exists(os.path.join(self.get_spec_dir, p)) for p in WEB_RESOURCE_DIRS)

    @property
    def exists_source(self):
        """Check in the source of the WebResource exists."""
        return os.path.exists(self.uri_to_path)

    def create_dataset_webresource_dirs(self):
        """Create all subdirectories for the WebResource based on spec."""
        for folder in WEB_RESOURCE_DIRS:
            full_path = os.path.join(self.get_spec_dir, folder)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

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
    def uri(self):
        """The uri of the object."""
        if not self._uri and self._source_path:
            self._uri = self.path_to_uri
        elif not self._uri and not self._path:
            raise ValueError("Either path or uri must be given in the constructor")
        return self._uri

    def get_cache_uri(path):
        """Get the Cache Source URI from the metadata."""
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
    def clean_uri(self):
        return self.uri.replace("urn:{}/".format(self.spec), "") if not self.is_cached else self.uri

    @property
    def uri_to_path(self):
        """Given the URI give back the path to the source WebResource."""
        path = None
        if self.is_cached:
            path = os.path.join(self.get_spec_dir, CACHE_DIR,
                                self.get_derivative_base_path())
        else:
            path = os.path.join(self.get_spec_dir, SOURCE_DIR, self.clean_uri)
        if path and not self._source_path:
            self._source_path = path
        return path

    def get_derivative_base_path(self, uri=None, kind="thumbnails"):
        """Create base path for the derivatives.

        Note that this does not include the size or mime-type extensions
        """
        if not uri:
            uri = self.uri
        sha = self.get_hash(uri)
        sub_dirs = re.findall('...?', sha)[:3]
        sub_dirs.insert(0, kind)
        sub_dirs.append(sha)
        return os.path.join(*sub_dirs)

    def get_thumbnail_path(self):
        pass

    def get_deepzoom_path(self):
        pass
