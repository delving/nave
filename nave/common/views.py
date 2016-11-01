import os

from django.conf import settings
from django.http.response import HttpResponse
from django.views.generic import RedirectView

from . import version


def nave_version(request):
    project_path = os.path.join(settings.PROJECT_ROOT)
    try:
        import git
        repo = git.Repo(project_path)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
    except ImportError:
        sha = short_sha = None
    content = """
            - nave_version = {nave_version}
            - project git-sha = {git_sha}
            - project git-sha-short = {short_sha}
            """.format(
                nave_version=version.__version__,
                git_sha=sha,
                short_sha=short_sha
            )
    return HttpResponse(content_type='text/plain', content=content)


class NarthexRedirectView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        resolve_url = self.request.META["HTTP_HOST"].split(':')[0]
        return "http://{}/narthex".format(resolve_url)
