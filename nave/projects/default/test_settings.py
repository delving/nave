from os.path import dirname, abspath, sep

try:
    from .settings import *
except ImportError:
    print("Unable to load the settings.py")
    raise

SITE_NAME = dirname(abspath(__file__)).split(sep)[-1]

########## DATABASE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    "default": {
        # Ends with "postgresql_psycopg2", "mysql", "sqlite3" or "oracle".
        "ENGINE": "django.db.backends.postgresql_psycopg2",  # "django.db.backends.postgresql_psycopg2",
        # DB name or path to database file if using sqlite3.
        "NAME": "{}".format(SITE_NAME),
        # Not used with sqlite3.
        "USER": "zemyatin",
        # Not used with sqlite3.
        "PASSWORD": "room-dait",
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": "",
        # Set to empty string for default. Not used with sqlite3.
        "PORT": "",
    }
}
########## END DATABASE CONFIGURATION