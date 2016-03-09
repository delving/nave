from django.views.generic import RedirectView


class NarthexRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        resolve_url = self.request.META["HTTP_HOST"].split(':')[0]
        return "http://{}/narthex".format(resolve_url)
