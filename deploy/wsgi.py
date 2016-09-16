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

os.environ['DJANGO_SETTINGS_MODULE'] = 'nave.projects.%(proj_name)s.settings'

application = Sentry(get_wsgi_application())

