
import logging

from django.views.generic import RedirectView

from webresource.webresource import WebResource


logger = logging.getLogger(__file__)


class WebResourceRedirectView(RedirectView):
    """
    This View determines if the WebResource exists and then redirects it to
    NGINX for serving.

    If the source web-resource exists but no derivatives they will be created
    on the fly.
    """
    permanent = False
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Retrieving the WebResource derivative URIs
        """
        uri = self.query_string.get('uri')
        hub_id = self.query_string.get('hubId')
        doc_type = self.query_string.get('docType', "thumbnail")
        width = self.query_string.get('width', "220")
        height = self.query_string.get('height', "220")
        # media_type = self.query_string.get('mediaType')
        # default_image = self.query_string.get('defaultImage')

        webresource = WebResource(uri=uri, hub_id=hub_id)
        redirect_uri = None
        if doc_type == 'thumbnail':
            redirect_uri = webresource.get_thumbnail_redirect(width, height)
        elif doc_type == "deepzoom":
            redirect_uri = webresource.get_deepzoom_redirect()
        # TODO: possibly later add route to source for logged in or APi token users
        return redirect_uri
