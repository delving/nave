# -*- coding: utf-8 -*-
"""Common settings and globals."""
from __future__ import absolute_import, unicode_literals

import os
import re
from collections import defaultdict
from datetime import timedelta
from os.path import abspath, dirname, join, normpath

from django.utils.translation import ugettext_lazy as _

print("Welcome to the Delving Nave. ({})".format(os.getpid()))

MIGRATION_MODULES = {
    'taggit': 'taggit.migrations',
}

# #######################
# MAIN DJANGO SETTINGS #
# #######################


# ######### PATH CONFIGURATION
# Absolute filesystem path to the Django project directory:

DJANGO_ROOT = dirname(abspath(__file__))

# Absolute filesystem path to the top-level project folder:
SITE_ROOT = dirname(DJANGO_ROOT)

BASEDIR = dirname(abspath(__file__))

PROJECT_ROOT = DJANGO_ROOT

# ######### END PATH CONFIGURATION


# ######### DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True

# ######### END DEBUG CONFIGURATION

APPEND_SLASH = True

# ######### MANAGER CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
# People who get code error notifications.
# In the format (('Full Name', 'email@example.com'),
#                ('Full Name', 'anotheremail@example.com'))
ADMINS = (
    ('Sjoerd Siebinga', 'sjoerd@delving.eu'),
    ('Eric van der Meulen', 'eric@delving.eu'),
    ('Jacob Lundqvist', 'jacob@delving.eu'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# ######### END MANAGER CONFIGURATION


# ######### GENERAL CONFIGURATION
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# See: https://docs.djangoproject.com/en/dev/ref/settings/#time-zone
TIME_ZONE = 'Europe/Amsterdam'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'nl'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = False

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

LOCALE_PATHS = [
    normpath(join(PROJECT_ROOT, 'common', 'locale'))
]

# ######### END GENERAL CONFIGURATION


# ###########################
# PATHS                    #
# ###########################

# ######### STATIC FILE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = normpath(join(PROJECT_ROOT, 'static'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/static/'

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
# STATICFILES_DIRS = (
#     normpath(join(DJANGO_ROOT, 'static')),
# )

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)
# ######### END STATIC FILE CONFIGURATION

# ######### MEDIA CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = normpath(join(PROJECT_ROOT, 'media'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'
# ######### END MEDIA CONFIGURATION

# ######### SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key should only be used for development and testing.
SECRET_KEY = r"(-%5-4d^f!5rz=kx!e6jfde_qzd9zi0g4tq%kb#@7+z#*-$ol-"
NEVERCACHE_KEY = (
    "310ab0e2-9a61-4e31-9de3-6af493b5c6cd8d32524f-618d-4aca-9665-"
    "1ab5ac91875d7e1adc60-cd9c-4f5b-b430-900"
)
# ######### END SECRET CONFIGURATION

# ######### SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "82.94.206.176"]
# ######### END SITE CONFIGURATION

# ######### TEMPLATE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
# List of processors used by RequestContext to populate the context.
# Each one should be a callable that takes the request object as its
# only parameter and returns a dictionary to add to the context.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
        # 'DEBUG': DEBUG,
        'OPTIONS': {
            'context_processors':
                [
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'django.template.context_processors.i18n',
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.template.context_processors.media',
                    'django.template.context_processors.csrf',
                    'django.template.context_processors.tz',
                    'django.template.context_processors.request',
                    'django.template.context_processors.static',
                    'nave.common.context_processors.current_url',
                ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            'loaders':
                [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                    'django.template.loaders.eggs.Loader'
                ],
            'builtins': ['overextends.templatetags.overextends_tags'],
        }
    },
]


# ######### END TEMPLATE CONFIGURATION


# ######### MIDDLEWARE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#middleware-classes
# List of middleware classes to use. Order is important; in the request phase,
# these middleware classes will be applied in the order given, and in the
# response phase the middleware will be applied in reverse order.
MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'nave.common.middleware.FallBackLanguageMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)

# Rosetta translations

ROSETTA_MESSAGES_PER_PAGE = 100

ROSETTA_AUTO_COMPILE = True

ROSETTA_WSGI_AUTO_RELOAD = True

ROSETTA_EXCLUDED_APPLICATIONS = (
    'filer', 'rest_framework', 'django_extensions', 'taggit', 'reversion'
)

# Every cache key will get prefixed with this value - here we set it to
# the name of the directory the project is in to try and use something
# project specific.
CACHE_MIDDLEWARE_KEY_PREFIX = 'nave'

# ######### END MIDDLEWARE CONFIGURATION

# Whether a user's session cookie expires when the Web browser is closed.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# ######### URL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'nave.urls'
# ######### END URL CONFIGURATION


# ######### CORS CONFIGURATION

# see: https://github.com/ottoyiu/django-cors-headers
CORS_ORIGIN_ALLOW_ALL = True
# CORS_URLS_REGEX = r'^/api/.*$'

# ######### END CORS CONFIGUATION

# ###############
# APPLICATIONS #
# ###############

DJANGO_APPS = (
    # Default Django apps:
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.redirects",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    'django.contrib.messages',
    'django.contrib.gis',
    # Useful template tags:
    # 'django.contrib.humanize',
    # Admin panel and documentation:
    'django.contrib.admindocs',
    # our very own common to override and add
    'nave.common',
    # django-suit to pimp the admin
    'suit',
    'suit_ckeditor',
    'django.contrib.admin',
    # 'admin_reorder',
)
# ######### APP CONFIGURATION


THIRD_PARTY_APPS = (
    'corsheaders',
    'django_extensions',
    'leaflet',
    'oauth2_provider',
    'raven.contrib.django.raven_compat',
    'rest_framework',
    'rest_framework.authtoken',
    'reversion',
    'rosetta',  # for translation
    'taggit',
    'watchman',
)

# Apps specific for this project go here.
LOCAL_APPS = (
    'nave.lod',
    'nave.void',
    'nave.search',
    'nave.webresource',
    'nave.virtual_collection',
)

# ########################
# OPTIONAL APPLICATIONS #
# ########################

# These will be added to ``INSTALLED_APPS``, only if available.
OPTIONAL_APPS = (
    # "debug_toolbar",
    # "debug_panel",
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS + OPTIONAL_APPS
# ######### END APP CONFIGURATION

# See: https://github.com/django-debug-toolbar/django-debug-toolbar#installation
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": ['debug_toolbar.panels.redirects.RedirectsPanel'],
    'SHOW_TEMPLATE_CONTEXT': True,
}

# Sentry / Raven configuration

RAVEN_CONFIG = {
    # dev setup override in production
    # 'dsn': '',
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    # 'release': raven.fetch_git_sha(SITE_ROOT),
}

IGNORABLE_404_URLS = (
    re.compile('/hm'),
)

# ######### LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# ######### END LOGGING CONFIGURATION
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'py.warnings': {
            'propagate': False,
            'handlers': ['null']
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'nave.common': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'nave.search': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'nave.lod': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'nave.void': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'nave.virtual_collection': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# ######### WSGI CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'wsgi.application'
# ######### END WSGI CONFIGURATION

# ############ REST Framework configuration

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
        'groups': 'Access to your groups'
    }
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
        'nave.search.renderers.XMLRenderer',
    ),
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    # rest_framework.permissions.IsAdminUser is another option
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'PAGINATE_BY': 10,
}

# ############ End


# ###################
# django extenions #
# ###################

GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}

# Always use IPython for shell_plus
SHELL_PLUS = "ipython"

IPYTHON_ARGUMENTS = [
    '--ext', 'django_extensions.management.notebook_extension',
    # '--debug',
]

# ########### End django extensions


# ###########################
# # Leaflet configuration   #
# ###########################

SERIALIZATION_MODULES = {
    'geojson': 'djgeojson.serializers'
}


# ########################
# DataSet configuration #
# ########################

RDF_USE_LOCAL_GRAPH = True

RDF_STORE_TRIPLES = False

RDF_DYNAMIC_CACHE = True

RDF_DEFAULT_FORMAT = 'nt'

RDF_SUPPORTED_NAMESPACES = {
    'http://purl.org/abm/sen': 'abm',
    'http://www.europeana.eu/schemas/ese/': 'europeana',
    'http://purl.org/dc/elements/1.1/': 'dc',
    'http://schemas.delving.eu/': 'delving',
    'http://purl.org/dc/terms/': 'dcterms',
    'http://www.delving.eu/namespaces/custom': 'custom',
    'http://www.musip.nl/': 'musip',
    'http://www.itin.nl/namespace': 'itin',
    'http://www.itin.nl/drupal': 'drup',
    'http://www.ab-c.nl/': 'abc',
    'http://delving.eu/namespaces/raw': 'raw',
    'http://www.icn.nl/schemas/icn/': 'icn',
    'http://schemas.delving.eu/aff/': 'aff',
    # 'http://schemas.delving.eu/abm/': 'abm',
    'http://www.w3.org/2004/02/skos/core#': 'skos',
    'http://dbpedia.org/ontology/': 'dbpedia-owl',
    'http://www.w3.org/2003/01/geo/wgs84_pos#': 'wgs84_pos',
    'http://xmlns.com/foaf/0.1/': 'foaf',
    'http://www.w3.org/2002/07/owl#': 'owl',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
    'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
    'http://www.europeana.eu/schemas/edm/': 'edm',
    'http://www.openarchives.org/ore/terms/': 'ore',
    'http://schemas.delving.eu/narthex/terms/': 'narthex',
    'http://schemas.delving.eu/nave/terms/': 'nave',
    'http://localhost:8000/resource/': 'devmode',
    'http://schemas.delving.eu/resource/ns/tib/': 'tib',
    'http://creativecommons.org/ns#': 'cc',
    'http://www.geonames.org/ontology#': 'gn',
    'http://rdvocab.info/ElementsGr2/': 'rda',
}

RDF_SUPPORTED_PREFIXES = defaultdict(list)
for ns, prefix in RDF_SUPPORTED_NAMESPACES.items():
    RDF_SUPPORTED_PREFIXES[prefix].append(ns)

RDF_EXCLUDED_PROPERTIES = [
    "http://schemas.delving.eu/narthex/terms/datasetMapToPrefix",
    "http://schemas.delving.eu/narthex/terms/datasetCharacter",
    "http://schemas.delving.eu/narthex/terms/datasetErrorTime",
    "http://schemas.delving.eu/narthex/terms/acceptanceOnly",
    "http://schemas.delving.eu/narthex/terms/synced",
    "http://schemas.delving.eu/narthex/terms/stateSourced",
    "http://schemas.delving.eu/narthex/terms/stateSaved",
    "http://schemas.delving.eu/narthex/terms/stateProcessed",
    "http://schemas.delving.eu/narthex/terms/stateProcessable",
    "http://schemas.delving.eu/narthex/terms/stateMappable",
    "http://schemas.delving.eu/narthex/terms/stateAnalyzed",
    "http://schemas.delving.eu/narthex/terms/publishOAIPMH",
    "http://schemas.delving.eu/narthex/terms/publishLOD",
    "http://schemas.delving.eu/narthex/terms/publishIndex",
    "http://schemas.delving.eu/narthex/terms/processedValid",
    "http://schemas.delving.eu/narthex/terms/processedInvalid",
    "http://schemas.delving.eu/narthex/terms/acceptanceOnly",
    "http://schemas.delving.eu/narthex/terms/actorOwner"
]

#  output search_label key: path in EDM tree (URIRef)

# todo convert to dict
EDM_API_INLINE_PREVIEW = {
    'http://schemas.delving.eu/nave/terms/objectNumber': 'tib_objectNumber',
    'http://schemas.delving.eu/nave/terms/hubId': 'delving_hubId',
    'http://purl.org/dc/elements/1.1/title': 'dc_title',
    'http://www.europeana.eu/schemas/edm/isShownBy': 'europeana_isShownBy',
    'http://purl.org/dc/elements/1.1/creator': 'dc_creator'
}

CONVERTERS_WITH_INLINE_PREVIEWS = ['tib']

INLINE_EDM_LINKS = True

# Search preview
# TODO add this option

# DETAIL VIEWS
RDF_CONTENT_DETAIL = {
    "ore_aggregation": "rdf/content_detail/ore_aggregation.html",
    "narthex_record": "rdf/content_detail/ore_aggregation.html",
    "gn_feature": "rdf/content_detail/gn_feature.html",
    "rce_rijksmonument": "rdf/content_detail/rce_RijksMonument.html",
}

# FOLDOUTS
RDF_CONTENT_FOLDOUTS = {
    "ore_aggregation": "rdf/content_foldout/lod-detail-foldout.html",
    "gn_feature": "rdf/content_foldout/gn_feature.html",
    "rce_rijksmonument": "rdf/content_foldout/rce_RijksMonument.html",
}


DEFAULT_V1_CONVERTER = "icn"
DEFAULT_V2_CONVERTER = "v2"

MLT_FIELDS = [
    "dc_subject.value",
    "dc_title.value",
    "dc_description.value",
    "edm_dataProvider.value"
]

MLT_DETAIL_ENABLE = True

MLT_BANNERS = {}

# ############################
#  IMAGE CONFIGURATION      #
# ############################

WEB_RESOURCE_BASE = '/tmp/webresource'

WEB_RESOURCE_MAX_SIZE = 500
WEB_RESOURCE_THUMB_SMALL = 220
WEB_RESOURCE_THUMB_LARGE = 500
WEB_RESOURCE_USE_RDF_BASE = True

RESOLVE_WEBRESOURCES_VIA_RDF = False

ZIPPED_SEARCH_RESULTS_DOWNLOAD_FOLDER = '/tmp/zips'


# ############################
# # Celery Broker settings.  #
# ############################

BULK_API_ASYNC = True

BROKER_URL = 'amqp://guest:guest@localhost:5672//'

CELERY_RESULT_BACKEND = 'amqp'  # 'amqp', 'redis'

CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'

CELERY_CONCURRENCY = 2

CELERY_IGNORE_RESULT = True

CELERY_ALWAYS_EAGER = False  # production should be false

CELERY_ACKS_LATE = True

CELERYBEAT_SCHEDULE = {
    'add-every-60-seconds': {
        'task': 'nave.webresource.tasks.create_webresource_dirs',
        'schedule': timedelta(seconds=60),
        'args': None
    },
}


class FacetConfig(object):
    """
    The configuration options for a facet entry
    """

    def __init__(self, es_field, label, size=50, sort_ascending=True):
        self.es_field = es_field
        self.label = label
        self.size = size
        self.sort_ascending = sort_ascending
        self.facet_link = None


FACET_CONFIG = [
    FacetConfig('dc_subject.raw', _("Subject")),
    FacetConfig('nave_province.raw', _("Province")),
    FacetConfig('edm_type.raw', _("Type")),
    FacetConfig('edm_dataProvider.raw', _("Type")),
    FacetConfig('legacy.delving_recordType.raw', _("Record Type")),
]


# CELERY_TASK_RESULT_EXPIRES = 18000

# ########################
# Leaflet map settings  #
# ########################
# latlng = L.latLng(52.374028073342, 4.899862287025)
LEAFLET_CONFIG = {
    # 'SPATIAL_EXTENT': (4.8998622870259, 52.374028073342, 7, 46),
    'DEFAULT_CENTER': (52.374028073342, 4.8998622870259),
    'DEFAULT_ZOOM': 7,
    'MIN_ZOOM': 3,
    'MAX_ZOOM': 20,
    'TILES': 'http://{s}.tile.osm.org/{z}/{x}/{y}.png',
    # 'ATTRIBUTION_PREFIX': 'Powered by django-leaflet',
    'MINIMAP': True,
    'RESET_VIEW': False
}

###################################
# WATCHMAN health configuration   #
###################################

WATCHMAN_CHECKS = (
    'watchman.checks.caches',
    'watchman.checks.databases',
    'watchman.checks.storage',
    'nave.common.watchman_checks.get_disk_space_status',
    'nave.common.watchman_checks.check_es_status',
    'nave.common.watchman_checks.check_fuseki_status',
    'nave.common.watchman_checks.check_celery_status',
)
