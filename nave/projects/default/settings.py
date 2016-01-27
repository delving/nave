# -*- coding: utf-8 -*-
"""Common settings and globals."""

from os.path import abspath, dirname, sep

from django.utils.translation import ugettext_lazy as _

# Get the Site name first:
from kombu import Queue, Exchange


SITE_NAME = dirname(abspath(__file__)).split(sep)[-1]
print(("Starting with settings from {}".format(SITE_NAME)))



##################
# BASE SETTINGS #
##################

# Allow settings to be shared between all nave projects to be loaded first.
# The remainder of this settings file contains project specific settings
try:
    from base_settings import *
except ImportError:
    print("Unable to load the base_settings.py. Please make sure the base_settings.py is on your "
          "sys path")
    raise

########################
# MAIN DJANGO SETTINGS #
########################


########## PATH CONFIGURATION

# Name of the directory for the project.
PROJECT_DIRNAME = SITE_NAME

PROJECT_ROOT = dirname(abspath(__file__))

# Add our project app to our pythonpath, this way we don't need to type our project
# name in our dotted import paths:
path.append(PROJECT_ROOT)
########## END PATH CONFIGURATION

########## END GENERAL CONFIGURATION

LANGUAGE_CODE = 'en'

########## SITE CONFIGURATION
# Hosts/domain names that are valid for this site
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "acc.{}.delving.org".format(SITE_NAME), "82.94.206.176"]
########## END SITE CONFIGURATION

########## FIXTURE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
# FIXTURE_DIRS = (
#     normpath(join(PROJECT_ROOT, 'fixtures')),
# )
########## END FIXTURE CONFIGURATION


########## MIDDLEWARE CONFIGURATION

# Every cache key will get prefixed with this value - here we set it to
# the name of the directory the project is in to try and use something
# project specific.
CACHE_MIDDLEWARE_KEY_PREFIX = PROJECT_DIRNAME

########## END MIDDLEWARE CONFIGURATION


################
# APPLICATIONS #
################

########## APP CONFIGURATION


# Apps specific for this project go here.
PROJECT_APPS = (
    "projects.default",
)


# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + PROJECT_APPS
########## END APP CONFIGURATION


##########################
# RDF store configuration #
##########################

RDF_STORE_PORT = 3030  # Port for triple store HTTP server

RDF_STORE_HOST = "http://localhost"

RDF_BASE_URL = "http://brabantcloud.nl"

RDF_STORE_DB = SITE_NAME

RDF_ROUTED_ENTRY_POINTS = []

###################
# Elastic search  #
###################

ES_URLS = ['localhost:9200']

ES_DISABLED = False  # useful for debugging

ES_TIMEOUT = 5

ES_ROWS = 20

#########################
# DataSet configuration #
#########################

NARTHEX_URL = "http://localhost:9000/narthex"
NARTHEX_API_KEY = "secret"
ORG_ID = 'delving'

SCHEMA_REPOSITORY = "http://schemas.delving.eu/"
DEFAULT_INDEX_SCHEMA = "icn"
ENABLED_SCHEMAS = ['abm', 'icn', 'tib']

#############################
## Celery Broker settings.  #
#############################

# queues and routes
CELERY_DEFAULT_QUEUE = SITE_NAME
CELERY_DEFAULT_EXCHANGE_TYPE = 'topic'
CELERY_DEFAULT_ROUTING_KEY = SITE_NAME

RECORD_QUEUE = "{}_records".format(SITE_NAME)
mapping_queue = "{}_mapping".format(SITE_NAME)
big_download_queue = "{}_download".format(SITE_NAME)
webresource_queue = "{}_webresource".format(SITE_NAME)

CELERY_QUEUES = (
    Queue(SITE_NAME, Exchange(SITE_NAME), routing_key='default'),
    Queue(RECORD_QUEUE, Exchange(RECORD_QUEUE), routing_key=RECORD_QUEUE),
    Queue(mapping_queue, Exchange(mapping_queue), routing_key=mapping_queue),
    Queue(big_download_queue, Exchange(big_download_queue), routing_key=big_download_queue),
    Queue(webresource_queue, Exchange(webresource_queue), routing_key=webresource_queue),
)


###################
# DEPLOY SETTINGS #
###################

########## SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
# Note: This key should only be used for development and testing.
SECRET_KEY = r"(-%5-4d^f!5rz=kx!e6jfde_qzd9zi0g4tq%kb#@7+z#*-$ol-"
NEVERCACHE_KEY = "310ab0e2-9a61-4e31-9de3-6af493b5c6cd8d32524f-618d-4aca-9665-1ab5ac91875d7e1adc60-cd9c-4f5b-b430-900"
########## END SECRET CONFIGURATION


# These settings are used by the default fabfile.py provided.
# Check fabfile.py for defaults.

FABRIC = {
    "EMAIL_HOST": "mx2.hostice.net",
    "SSH_USER": "fab_user",  # SSH username
    # "SSH_PASS": "9@?[ZMh26VcF3jKw§ucy3!!@",  # SSH password (consider key-based authentication)
    "SSH_KEY_PATH": "~/.ssh/id_rsa",  # Local path to SSH key file, for key-based auth
    "ACC_HOSTS": ["82.94.206.176"],  # List of hosts to deploy to
    "PROD_HOSTS": ["82.94.206.176"],  # List of hosts to deploy to
    "VIRTUALENV_HOME": "/home/fab_user",  # Absolute remote path for virtualenvs
    "PROJECT_NAME": "{}".format(SITE_NAME),  # Unique identifier for project
    "REQUIREMENTS_PATH": "requirements/base.txt",  # Path to pip requirements, relative to project
    "SETTINGS_PATH": "projects/{}/settings".format(SITE_NAME),  # Path to pip requirements, relative to project
    "GUNICORN_PORT": 8009,  # Port gunicorn will listen on
    "NARTHEX_PORT": 9010,  # The port narthex will listen to
    "ORG_ID": "delving",  # The Culture Commons
    "HUB_NODE": "playground",  # The node this organisation
    "LOCALE": "en_GB.UTF-8",  # Should end with ".UTF-8"
    "ACC_HOSTNAME": "acc.{}.delving.org".format(SITE_NAME),  # Host for public site.
    "PROD_HOSTNAME": "prod.{}.delving.org".format(SITE_NAME),  # Host for public site.
    "REPO_URL": "git@github.com:delving/nave_private.git",  # Git or Mercurial remote repo URL for the project
    "DB_PASS": "9@?[ZMh26VcF3jKwucy4",  # Live database password
    "ADMIN_PASS": "9@?[ZMh26VcF3jKwucy5",  # Live admin user password
    "SECRET_KEY": SECRET_KEY,
    "NEVERCACHE_KEY": NEVERCACHE_KEY,
}

####################################
#    Django Suit Configuration     #
####################################

# Django Suit configuration example
SUIT_CONFIG = {
    # header
    'ADMIN_NAME': 'Nave Admin',
    # 'HEADER_DATE_FORMAT': 'l, j. F Y',
    # 'HEADER_TIME_FORMAT': 'H:i',

    # forms
    # 'SHOW_REQUIRED_ASTERISK': True,  # Default True
    # 'CONFIRM_UNSAVED_CHANGES': True, # Default True

    # menu
    # 'SEARCH_URL': '/admin/auth/user/',
    # 'MENU_ICONS': {
    #    'sites': 'icon-leaf',
    #    'auth': 'icon-lock',
    # },
    # 'MENU_OPEN_FIRST_CHILD': True, # Default True
    # 'MENU_EXCLUDE': ('auth.group',),
    # 'MENU': (
    #     'sites',
    #     {'app': 'auth', 'icon':'icon-lock', 'models': ('user', 'group')},
    #     {'label': 'Settings', 'icon':'icon-cog', 'models': ('auth.user', 'auth.group')},
    #     {'label': 'Support', 'icon':'icon-question-sign', 'url': '/support/'},
    # ),

    # misc
    'LIST_PER_PAGE': 15
}



##################
# LOCAL SETTINGS #
##################

# Allow any settings to be defined in local_settings.py which should be
# ignored in your version control system allowing for settings to be
# defined per machine.
try:
    from local_settings import *
except ImportError:
    print("Unable to load the local_settings.py. Please create one from local_settings.py.template.")
    raise
