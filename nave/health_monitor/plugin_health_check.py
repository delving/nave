# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import shutil
from time import sleep

from django.conf import settings
from health_check.backends.base import BaseHealthCheckBackend, ServiceUnavailable, ServiceReturnedUnexpectedResult
from health_check.plugins import plugin_dir


class DiskSpaceHealth(BaseHealthCheckBackend):

    @staticmethod
    def get_disk_space_status(total=None, used=None, free=None):
        if None in [total, used, free]:
            total, used, free = shutil.disk_usage('/')
        percentage_free = ((free / total) * 100)
        if not percentage_free > 10.0:
            raise ServiceUnavailable("Only {} % free space available".format(percentage_free))
        if not percentage_free > 30.0:
            raise ServiceReturnedUnexpectedResult("Only {} % free space available".format(percentage_free))
        return True

    def check_status(self):
        return self.get_disk_space_status()


plugin_dir.register(DiskSpaceHealth)


class ElasticSearchHealth(BaseHealthCheckBackend):

    def check_status(self):
        urls = settings.ES_URLS
        try:
            from search import get_es_client
            es = get_es_client()
            return es.indices.exists(settings.SITE_NAME)
        except Exception as e:
            raise ServiceUnavailable("Connection Error")

plugin_dir.register(ElasticSearchHealth)


class FusekiHealth(BaseHealthCheckBackend):

    def check_status(self):
        try:
            import requests
            resp = requests.get("{}:{}/$/ping".format(settings.RDF_STORE_HOST, settings.RDF_STORE_PORT))
            return resp.ok
        except Exception as e:
            raise ServiceUnavailable("Connection Error")

plugin_dir.register(FusekiHealth)


class CeleryHealthCheck(BaseHealthCheckBackend):

    def check_status(self):
        timeout = getattr(settings, 'HEALTHCHECK_CELERY_TIMEOUT', 3)

        try:
            from .tasks import add
            result = add.apply_async(args=[4, 4], expires=datetime.now() + timedelta(seconds=timeout))
            now = datetime.now()
            while (now + timedelta(seconds=3)) > datetime.now():
                print("            checking....")
                if result.ready():
                    # result.forget()
                    return True
                sleep(0.5)
        except IOError:
            pass
        raise ServiceUnavailable("Unknown error")

plugin_dir.register(CeleryHealthCheck)
