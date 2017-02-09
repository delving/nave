# -*- coding: utf-8 -*-

from .convertors import ICNConverter, TIBConverter, ABMConverter, \
     ESEConverter, EDMStrictConverter, EDMConverter, DefaultAPIV2Converter

REGISTERED_CONVERTERS = {
    "icn": ICNConverter,
    "tib": TIBConverter,
    "abm": ABMConverter,
    "ese": ESEConverter,
    "edm": EDMConverter,
    "edm-strict": EDMStrictConverter,
    "v2": DefaultAPIV2Converter,
    "raw": None
}
