# coding=utf-8
"""
Django command to load an ES actions file directly.
"""
import json

from django.conf import settings
from django.core.management import BaseCommand
from elasticsearch import helpers

from nave.search import es_client


class Command(BaseCommand):


    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            help='path to es actions file.'
        )

    def handle(self, *args, **options):

        actions_file = options['path']
        index = settings.SITE_NAME
        lines = 0
        buffer = []
        with open(actions_file, 'r') as es_actions:
            for action in es_actions:
                if action.startswith('{"_op_type":'):
                    buffer.append(json.loads(action))
                    lines += 1
                if lines % 500 == 0:
                    try:
                        self.stdout.write('proccessed {} lines'.format(lines))
                        helpers.bulk(client=es_client, actions=buffer, index=index)
                    except Exception as e:
                        print(e)
                        print(lines)
                    finally:
                        buffer[:] = []
        # save remaining records
        helpers.bulk(client=es_client, actions=buffer, index=index)
        self.stdout.write('Start loading data actions into ElasticSearch.')
        self.stdout.write('loaded {} records into ElasticSearch'.format(lines))
