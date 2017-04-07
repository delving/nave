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
            '--spec',
            help='Spec name to be deleted.'
        )
        parser.add_argument(
            '--index',
            help='index to be used.'
        )

    def handle(self, *args, **options):
        spec = options['spec']
        index = options['index']
        response = es_client.delete_by_query(
            index=index,
            body="""
                {{
                    "query": {{
                        "query_string" : {{
                            "default_field" : "system.spec.raw",
                            "query" : "{spec}"
                    }}
                }}
            }}
            """.format(spec=spec),
            # q="system.spec.raw:\"{}\"".format(spec),
        )
        sys.stdout.write(
            "Deleted {} from Search index with message: {}".format(
                spec, response
        ))
