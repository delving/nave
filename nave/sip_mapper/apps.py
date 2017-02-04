# -*- coding: utf-8 -*-
"""
This module configures the Human readable name for this module.

It will also be used in the admin section.
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class VirtualCollectionConfig(AppConfig):
    name = 'Sip Mapper'
    verbose_name = _("Aggregated Metadata")
