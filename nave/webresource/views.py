
import logging

from django.conf import settings
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
        uri = self.request.GET.get('uri')
        hub_id = self.request.GET.get('hubId')
        doc_type = self.request.GET.get('docType', "thumbnail")
        width = self.request.GET.get('width', 220)
        height = self.request.GET.get('height', 220)
        spec = self.request.GET.get('spec')

        if not isinstance(width, int):
            width = int(width)
        if not isinstance(height, int):
            height = int(height)

        domain = self.request.META['HTTP_HOST']
        if settings.DEBUG:
            domain = domain.replace(':8000', '')

        # media_type = self.query_string.get('mediaType')
        # default_image = self.query_string.get('defaultImage')
        if not spec and hub_id:
            org_id, spec, local_id = hub_id.split('_')

        webresource = WebResource(uri=uri, hub_id=hub_id, spec=spec, domain=domain)
        redirect_uri = None
        if doc_type == 'thumbnail':
            redirect_uri = webresource.get_thumbnail_redirect(width, height)
        elif doc_type == "deepzoom":
            redirect_uri = webresource.get_deepzoom_redirect()
        # TODO: possibly later add route to source for logged in or APi token users
        return redirect_uri
