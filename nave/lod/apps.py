# -*- coding: utf-8 -*- 
"""
This module configures the Human readable name for this module.

It will also be used in the admin section.
"""
from django.apps import AppConfig


class LoDConfig(AppConfig):
    name = 'lod'
    verbose_name = "Linked Open Data"
