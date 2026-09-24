"""
WSGI config for nave project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

from __future__ import unicode_literals

import os

from django.core.wsgi import get_wsgi_application
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nave.settings")

application = get_wsgi_application()

# Sentry reads its DSN from RAVEN_CONFIG; with none configured the wrapper is
# a no-op, so this is safe on a deployment that does not use it.
application = Sentry(application)
