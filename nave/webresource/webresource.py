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
import os
import re



class WebResource:

    def __init__(self, spec, base_dir=None, settings=None, org_id=None):
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

    def create_dataset_webresource_dirs(self):
        """Create all subdirectories for the WebResource based on spec."""
        dirs = ["source", "cache", "derivatives/thumbnails",
                "derivatives/deepzoom", "rdf", "nathex"]
        for folder in dirs:
            full_path = os.path.join(self.get_spec_dir, folder)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

    @staticmethod
    def get_hash(uri):
        """Create SHA256 hash from a URI.
        :param uri: The
        """
        return hashlib.sha256(uri.encode("utf-8")).hexdigest()

    def get_derivative_base_path(self, uri, kind="thumbnails"):
        """Create base path for the derivatives.

        Note that this does not include the size or mime-type extensions
        """
        sha = self.get_hash(uri)
        sub_dirs = re.findall('...?', sha)[:3]
        return os.path.join(kind, *sub_dirs, sha)
