# -*- coding: utf-8 -*- 
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<spec> <path to xml>'
    help = 'bulk load xml files processed by Narthex'

    def handle(self, *args, **options):
        spec = args[0]
        processed_xml = args[1]

        self.stdout.write('Starting to loading EDM for spec {}'.format(spec))
        from lod.utils.narthex_bulk_loader import NarthexBulkLoader
        loader = NarthexBulkLoader()
        load_results = loader.process_narthex_file(spec=spec, path=processed_xml)
        self.stdout.write("result bulkloading: {}".format(load_results))
        self.stdout.write('Finished to loading EDM for spec {}'.format(spec))


