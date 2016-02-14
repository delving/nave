
import logging

from django.http import HttpResponseBadRequest, HttpResponsePermanentRedirect, HttpResponseSeeOtherRedirect
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
        Do ContentNegotiation for some resource and
        redirect to the appropriate place
        """
        label = self.kwargs.get('label')
        type_ = self.kwargs.get('type_')
        url_kwargs = {'label': label}
        extension_ = self.kwargs.get('extension')
        mimetype = get_lod_mime_type(extension_, self.request)

        if mimetype and mimetype in RDF_SUPPORTED_MIME_TYPES:
            path = "lod_data_detail"
            url_kwargs['extension'] = mime_to_extension(mimetype)
        elif USE_EDM_BINDINGS and type_ in ["aggregation"]:
            path = "edm_lod_page_detail"
            return reverse(path, kwargs=url_kwargs)
        else:
            path = "lod_page_detail"

        if type_:
            path = "typed_{}".format(path)
            url_kwargs['type_'] = type_

        return reverse(path, kwargs=url_kwargs)

    def get(self, request, *args, **kwargs):
        url = self.get_redirect_url(*args, **kwargs)
        if url:
            if self.permanent:
                return HttpResponsePermanentRedirect(url)
            else:
                return HttpResponseSeeOtherRedirect(url)
        else:
            logger.warning('Gone: %s', self.request.path,
                           extra={
                               'status_code': 410,
                               'request': self.request
                           })
            return HttpResponseBadRequest()
