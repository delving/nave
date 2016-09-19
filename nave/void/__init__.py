# -*- coding: utf-8 -*-
from nave.void.converters import ICNConverter, ABMConverter, ESEConverter, EDMStrictConverter, EDMConverter, \
    DefaultAPIV2Converter

# Verbose name configuration for this app
default_app_config = 'nave.void.apps.VoidConfig'

REGISTERED_CONVERTERS = {
    "icn": ICNConverter,
    "abm": ABMConverter,
    "ese": ESEConverter,
    "edm": EDMConverter,
    "edm-strict": EDMStrictConverter,
    "v2": DefaultAPIV2Converter,
    "raw": None
}

def get_es():
    from nave.search import get_es_client
    return get_es_client()
