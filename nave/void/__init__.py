# -*- coding: utf-8 -*- 
from django.conf import settings
from elasticsearch import Elasticsearch

from void.convertors import ICNConverter, TIBConverter, ABMConverter, ESEConverter, EDMStrictConverter, EDMConverter, \
    DefaultAPIV2Converter

es = Elasticsearch(
    hosts=settings.ES_URLS
)


def get_es():
    return es

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
