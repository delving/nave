# -*- coding: utf-8 -*- 
from django.core.management.base import BaseCommand
from rdflib import URIRef, Graph, RDF
from rdflib.namespace import SKOS

from void.utils.bulk_loader import EDMBulkLoader


class Command(BaseCommand):
    args = '<spec> <path to xml>'
    help = 'bulk load xml files processed by Narthex'

    def handle(self, *args, **options):
        spec = args[0]
        processed_xml = args[1]

        self.stdout.write('Starting to loading EDM for spec {}'.format(spec))
        loader = EDMBulkLoader(spec, processed_xml)
        load_results = loader.parse_narthex_xml('admin')
        self.stdout.write("result bulkloading: {}".format(load_results))
        self.stdout.write('Finished to loading EDM for spec {}'.format(spec))


