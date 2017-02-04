import os
from django.conf import settings

def get(key, default):
    """Get the key from settings and otherwise return the default.

    The load order is as follows:
        * environment variables
        * default from DJANGO_SETTINGS_MODULE
        * default from here

    When in test mode settings from the test_settings dictionary is used.
    """
    setting = getattr(settings, key, default)
    if key in os.environ:
        env_val = os.environ.get(key, setting)
        print(env_val)
        if isinstance(default, bool):
            env_val = True if env_val.lower() == "true" else False
        setting = env_val
    return setting


"""
Enable the routes to Narthex or disable this functionality completely.
"""
ENABLE_NARTHEX = get('ENABLE_NARTHEX', True)
