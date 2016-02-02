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
ALLOWED_HOSTS = ["localhost", "acc.{}.delving.org".format(SITE_NAME), "vagrant.localhost",
                 "192.168.33.10"]
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
    "projects.vagrant",
)


# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + PROJECT_APPS
########## END APP CONFIGURATION


##########################
# RDF store configuration #
##########################

RDF_STORE_PORT = 3030  # Port for triple store HTTP server

RDF_STORE_HOST = "http://localhost"

RDF_BASE_URL = "http://vagrant.localhost"

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

ORG_ID = 'delving'
FILE_WATCH_BASE_FOLDER = '/tmp'
ZIPPED_SEARCH_RESULTS_DOWNLOAD_FOLDER = "/tmp"

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
SECRET_KEY = "l#5lyn$-z@ygw$uj-*+4%%rmz5j25btvud5v_^p3(5x$-p1_(k"
NEVERCACHE_KEY = "uj$_u7wg34ufb3zdv_*bcd@2s+e43eu^+!890vf$m*)gw8rg13"
########## END SECRET CONFIGURATION


# These settings are used by the default fabfile.py provided.
# Check fabfile.py for defaults.

FABRIC = {
    "EMAIL_HOST": "mx2.hostice.net",
    "SSH_USER": "vagrant",  # SSH username
    "SSH_PASS": "vagrant",  # SSH password (consider key-based authentication)
    # "SSH_KEY_PATH": "~/.ssh/id_rsa",  # Local path to SSH key file, for key-based auth
    "ACC_HOSTS": ["192.168.33.10"],  # List of hosts to deploy to
    "PROD_HOSTS": ["192.168.33.10"],  # List of hosts to deploy to
    "VIRTUALENV_HOME": "/home/{}".format(SITE_NAME),  # Absolute remote path for virtualenvs
    "PROJECT_NAME": "{}".format(SITE_NAME),  # Unique identifier for project
    "REQUIREMENTS_PATH": "requirements/base.txt",  # Path to pip requir[[ements, relative to project
    "SETTINGS_PATH": "projects/{}/settings".format(SITE_NAME),  # Path to pip requirements, relative to project
    "GUNICORN_PORT": 8001,  # Port gunicorn will listen on
    "NARTHEX_PORT": 9001,  # The port narthex will listen to
    "ZIPPED_SEARCH_RESULTS_DOWNLOAD_FOLDER": ZIPPED_SEARCH_RESULTS_DOWNLOAD_FOLDER,
    "RDF_BASE_URL": RDF_BASE_URL,
    "RDF_STORE_HOST": RDF_STORE_HOST,
    "ORG_ID": "vagrant",  # The Culture Commons
    "HUB_NODE": "vagrant",  # The node this organisation
    "LOCALE": "en_US.UTF-8",  # Should end with ".UTF-8"
    "ACC_HOSTNAME": "vagrant.localhost acc.{}.delving.org".format(SITE_NAME),  # Host for public site.
    "PROD_HOSTNAME": "prod.{}.delving.org".format(SITE_NAME),  # Host for public site.
    "REPO_URL": "https://github.com/delving/nave.git",  # Git or Mercurial remote repo URL for the project
    "GIT_BRANCH": "feature/vagrant_support",
    "SENTRY_DSN": "https://bea553a71cc54834a4f03507a92f02a1:5b093ba2516b49bd85f103f2aa02239e@app.getsentry.com/51537",
    "ACC_NAVE_AUTH_TOKEN": "4fc894433b3b914356f8a6887b39fcb26f249026",
    "PROD_NAVE_AUTH_TOKEN": "4fc894433b3b914356f8a6887b39fcb26f249026",
    "ACC_ES_CLUSTERNAME": "vagrant",
    "PROD_ES_CLUSTERNAME": "vagrant",
    "DB_PASS": "vagrant",  # Live database password
    "ADMIN_PASS": "vagrant",  # Live admin user password
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
