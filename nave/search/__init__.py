# -*- coding: utf-8 -*-
"""
"""
from collections import namedtuple

# Verbose name configuration for this app
default_app_config = 'nave.search.apps.SearchConfig'

LayoutItem = namedtuple("LayoutItem", ["name", "i18n"])
