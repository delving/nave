__version__ = "0.9.7-SNAPSHOT"


def get_version():
    """Return a version tuple of the app that can be cached."""
    import os
    from django.conf import settings
    project_path = os.path.join(settings.PROJECT_ROOT)
    try:
        import git
        repo = git.Repo(project_path)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
    except ImportError:
        sha = short_sha = None
    return __version__, sha, short_sha


__app_version__ = get_version()
