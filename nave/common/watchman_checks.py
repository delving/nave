# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import shutil
import sys
from time import sleep
import traceback

from django.conf import settings
from watchman.decorators import check

from nave.search import get_es_client

@check
def nave_version():
    nave_path = os.path.join(settings.SITE_ROOT)
    try:
        import git
        from . import version
        repo = git.Repo(nave_path)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
    except ImportError:
        sha = short_sha = None
    return {
        'version_nave': {
            'ok': True,
            'version': version.__version__,
            'sha': sha,
            'short_sha': short_sha,
        }
    }

@check
def project_version():
    project_path = os.path.join(settings.PROJECT_ROOT)
    try:
        import git
        repo = git.Repo(project_path)
        sha = repo.head.object.hexsha
        short_sha = repo.git.rev_parse(sha, short=8)
    except ImportError:
        sha = short_sha = None
    return {
        'version_project': {
            'ok': True,
            'name': settings.SITE_NAME,
            'sha': sha,
            'short_sha': short_sha,
        }
    }

@check
def get_disk_space_status():
    total, used, free = shutil.disk_usage('/')
    percentage_free = ((free / total) * 100)
    status_ok = True
    message = ""
    if not percentage_free > 10.0:
        status_ok = False
        message = "Only {} % free space available".format(percentage_free)
    if not percentage_free > 30.0:
        message = "Only {} % free space available".format(percentage_free)
    return {
        'disk_usage': {
            'ok': status_ok,
            'message': message,
            'total': total,
            'percentage_free': percentage_free,
            'used': used,
            'free': free,
        }
    }


@check
def check_es_status():
    ok_status = True
    message = ""
    try:
        es = get_es_client()
        es.indices.exists(settings.SITE_NAME)
    except Exception as e:
        message = e
    return {
        'elasticsearch': [
            {
                settings.SITE_NAME: {
                    'ok': ok_status,
                    'message': message,
                }
            }
        ]
    }


@check
def check_fuseki_status():
    import requests
    fuseki_ok = True
    database_ok_status = True
    service_message = ""
    database_message = ""
    service_error = ""
    database_error = ""
    try:
        response = requests.get(
            "{}:{}/$/ping".format(
                settings.RDF_STORE_HOST,
                settings.RDF_STORE_PORT
            )
        )
        if response.status_code != 200:
            fuseki_ok = False
    except Exception as ex:
        type_, value_, traceback_ = sys.exc_info()
        fuseki_ok = False
        service_error = str(value_)
        service_message = traceback.format_exc()
    try:
        response = requests.get(
            "{}:{}/{}/sparql?query=ask+where+{{%3Fs+%3Fp+%3Fo}}&output=json&stylesheet=".format(
                settings.RDF_STORE_HOST,
                settings.RDF_STORE_PORT,
                settings.RDF_STORE_DB,
            )
        )
        if response.status_code != 200:
            database_ok_status = False
    except Exception as ex:
        type_, value_, traceback_ = sys.exc_info()
        database_ok_status = False
        database_error = str(value_)
        database_message = traceback.format_exc()
    return {
        'fuseki': [
            {
                'service': {
                    'ok': fuseki_ok,
                    'error': service_error,
                    'traceback': service_message,
                }
            },
            {
                'database': {
                    'ok': database_ok_status,
                    'database_name': settings.RDF_STORE_DB,
                    'error': database_error,
                    'traceback': database_message,
                }
            }
        ]
    }


@check
def check_celery_status():
    timeout = getattr(settings, 'HEALTHCHECK_CELERY_TIMEOUT', 3)
    ok_status = True
    message = ""
    try:
        from .tasks import add
        result = add.apply_async(
            args=[4, 4], expires=datetime.now() + timedelta(seconds=timeout)
        )
        now = datetime.now()
        while (now + timedelta(seconds=3)) > datetime.now():
            if result.ready():
                # result.forget()
                break
            sleep(0.5)
    except Exception:
        # raise ServiceUnavailable("Unknown error")
        message = traceback.format_exc()
        ok_status = False
    return {
        'celery': {
            'ok': ok_status,
            'traceback': message,
        }
    }
