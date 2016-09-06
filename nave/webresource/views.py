
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
        from .webresource import WebResource
        try:
            return WebResource.get_redirect_url(self.request.build_absolute_uri())
        except ValueError as ve:
            return reverse("webresource_docs")


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
