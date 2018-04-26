import os

from django.conf import settings
from django.http.response import HttpResponse
from django.views.generic import RedirectView

from nave.lod.utils.resolver import RDFRecord

from . import version

def whoami(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    ip_filters = RDFRecord.get_filters_by_ip(request)
    content = """
        - forwarded = {}
        - forward_chain = {}
        - remote address = {}
        - ip_filter = {}
        - filters = []
    """.format(
        x_forwarded,
        x_forwarded.split(',')[0] if x_forwarded else None,
        request.META.get('REMOTE_ADDR'),
        RDFRecord.get_client_ip(request),
        ip_filters
    )
    return HttpResponse(content_type='text/plain', content=content)


def nave_version(request):
    project_path = os.path.join(settings.PROJECT_ROOT)
    nave_version, sha, short_sha = version.get_version()
    content = """
            - nave_version = {nave_version}
            - project git-sha = {git_sha}
            - project git-sha-short = {short_sha}
            """.format(
                nave_version=nave_version,
                git_sha=sha,
                short_sha=short_sha
            )
    return HttpResponse(content_type='text/plain', content=content)


class NarthexRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        resolve_url = self.request.META["HTTP_HOST"].split(':')[0]
        return "http://{}/narthex".format(resolve_url)
