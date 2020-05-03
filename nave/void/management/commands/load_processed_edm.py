# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            'spec',
            type=str,
            help='The datasets spec.'
        )
        parser.add_argument(
            'processed_xml',
            type=str,
            help='The full path to the narthex processed xml file.'
        )
        parser.add_argument(
            '--index',
            default=settings.INDEX_NAME,
            help='index to be used.'
        )


    def handle(self, *args, **options):
        spec = options['spec']
        processed_xml = options['processed_xml']
        index = options['index']

        self.stdout.write('Starting to loading EDM for spec {}'.format(spec))
        from nave.lod.utils.narthex_bulk_loader import NarthexBulkLoader
        loader = NarthexBulkLoader()
        load_results = loader.process_narthex_file(
            spec=spec,
            path=processed_xml,
            console=True,
            index=index
        )
        self.stdout.write("result bulkloading: {}".format(load_results))
        self.stdout.write('Finished to loading EDM for spec {}'.format(spec))
