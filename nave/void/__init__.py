# -*- coding: utf-8 -*-
from django.conf import settings
from elasticsearch import Elasticsearch


es = Elasticsearch(
    hosts=settings.ES_URLS
)

def get_es():
    return es
