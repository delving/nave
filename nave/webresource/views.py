from django.shortcuts import render
from django.views.generic import RedirectView


class WebResourceRedirectView(RedirectView):
    """
    The Redirect view does the content negotiation for a Linked Open Data request.

    When no content-type is requested or no content-extension specified, all traffic will be routed to the HTML view
    at '/page'.

    When a content type or extension is specified, all traffic will be routed to the data view
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
                return http.HttpResponsePermanentRedirect(url)
            else:
                return HttpResponseSeeOtherRedirect(url)
        else:
            logger.warning('Gone: %s', self.request.path,
                           extra={
                               'status_code': 410,
                               'request': self.request
                           })
