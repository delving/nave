# -*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from rdflib import URIRef, Graph, RDF
from rdflib.namespace import SKOS

from nave.lod.utils.narthex_bulk_loader import NarthexBulkLoader


class Command(BaseCommand):
    args = ''
    help = 'bulk load xml files processed by Narthex'

    def add_arguments(self, parser):
        parser.add_argument(
            '--index',
            default=settings.SITE_NAME,
            help='index to be used.'
        )
        parser.add_argument(
            '--path',
            default="~/NarthexFiles"
        )

    def handle(self, *args, **options):
        index = options['index']
        path = options['path']
        start = datetime.now()
        self.stdout.write('Starting to loading EDM for orgId {}'.format(settings.ORG_ID))
        loader = NarthexBulkLoader(index=index, narthex_base=path)
        load_results = loader.walk_all_datasets()
        self.stdout.write("result bulkloading: {}".format(load_results))
        self.stdout.write('Finished to loading EDM for orgId {} in {} seconds.'.format(
            settings.ORG_ID,
            datetime.now() - start
        ))


