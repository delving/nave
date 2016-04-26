# -*- coding: utf-8 -*- 
from django.conf import settings


es = Elasticsearch(
    hosts=settings.ES_URLS
)


def get_es():
    return es