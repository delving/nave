
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic import RedirectView


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
        width = self.request.GET.get('width', None)
        height = self.request.GET.get('height', None)
        spec = self.request.GET.get('spec')

        if not spec:
            return reverse("webresource_docs")
        elif not uri and not hub_id:
            return reverse("webresource_docs")

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

        domain = self.request.META['HTTP_HOST']
        # if settings.DEBUG:
            # domain = domain.replace(':8000', '')

        # media_type = self.query_string.get('mediaType')
        # default_image = self.query_string.get('defaultImage')
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


class DeepZoomRedirectView(RedirectView):
    """Custom redirect to deal with tiles request of DeepZoom viewers."""
    # permanent = False
    # query_string = False

    def get_redirect_url(self, *args, **kwargs):
        urn = kwargs['urn']
        spec = urn.split('/')[0].replace('urn:', '')
        domain = self.request.META['HTTP_HOST']
        return 'http://localhost:8000'
        from .webresource import WebResource
        if urn.endswith('.dzi'):
            wr = WebResource(uri=urn, spec=spec, domain=domain)
            return wr.get_deepzoom_redirect()
        elif '_files' in urn:
            urn, tile_path  = urn.split('_files', maxsplit=1)
            wr = WebResource(uri=urn, spec=spec, domain=domain)
            return wr.get_deepzoom_tile_path(tile_path=tile_path)


def webresource_docs(request):
    from django.http.response import HttpResponse
    content = """
            Acceptance parameters:

            - uri = link to uri. Can be both local as urn/http or remote for caching
            - hubId = the hubId that this image needs to be linked to. (Optional)
            - docType = of the returned derivative. (Optional) default is thumbnail Options:
                - thumbnail
                - deepzoom
            - width = the width of the thumbnail.  (Optional)
            - height = the height of the thumbnail. (Optional) Max size is 1000.
                - When only one of height and width is give it is squared with both.
            - spec = the spec the image. (Required)
            """
    return HttpResponse(content_type='text/plain', content=content)
