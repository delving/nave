from __future__ import unicode_literals
from os.path import dirname

import raven

SECRET_KEY = "%(secret_key)s"

DEBUG = %{debug_mode}

DATABASES = {
    "default": {
        # Ends with "postgresql_psycopg2", "mysql", "sqlite3" or "oracle", "postgis".
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        # DB name or path to database file if using sqlite3.
        "NAME": "%(proj_name)s",
        # Not used with sqlite3.
        "USER": "%(proj_name)s",
        # Not used with sqlite3.
        "PASSWORD": "%(db_pass)s",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "127.0.0.1",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}

RAVEN_CONFIG = {
    'dsn': "%(sentry_dsn)s",
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(dirname(dirname(dirname(dirname(__file__))))),
}

EMAIL_HOST = "%(email_host)s"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTOCOL", "https")

CACHE_MIDDLEWARE_SECONDS = 60

TIMEOUT = 300

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
        "KEY_PREFIX": "%(proj_name)s",
    }
}

# NARTHEX_URL = "http://localhost:%(narthex_port)s/narthex"

FILE_WATCH_BASE_FOLDER = "%(file_watch_base_folder)s"

RDF_STORE_HOST = "%(rdf_store_host)s"

RDF_BASE_URL = "%{rdf_base_url}"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
