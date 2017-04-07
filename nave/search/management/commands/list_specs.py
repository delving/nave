# coding=utf-8
"""
Django command to load an ES actions file directly.
"""
import json
import sys

from django.conf import settings
from django.core.management import BaseCommand
from elasticsearch import helpers

from nave.search import es_client


class Command(BaseCommand):


    def add_arguments(self, parser):
        parser.add_argument(
            '--index',
            default=settings.SITE_NAME,
            help='index to be used.'
        )

    def handle(self, *args, **options):
        index = options['index']
        from elasticsearch_dsl import Search, A
        s = Search(using=es_client, index=index)
        a = A('terms', field='system.spec.raw')
        s.aggs.bucket('specs', a)
        response = s.execute()
        for spec in response.aggregations.specs.buckets:
            sys.stdout.write(
                "{} => {}\n".format(
                    spec.key, spec.doc_count
            ))
