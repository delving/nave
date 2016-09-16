# -*- coding: utf-8 -*- 
"""
This module configures the Human readable name for this module.

It will also be used in the admin section.
"""
from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'nave.search'
    verbose_name = "Nave Search API"
