# -*- coding: utf-8 -*-
"""
This module configures the Human readable name for this module.

It will also be used in the admin section.
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WebResourceConfig(AppConfig):
    name = 'nave.webresource'
    verbose_name = _("WebResource App")
