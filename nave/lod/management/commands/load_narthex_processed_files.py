# -*- coding: utf-8 -*-
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from nave.lod.utils.narthex_bulk_loader import NarthexBulkLoader


class Command(BaseCommand):
    args = ''
    help = 'bulk load xml files processed by Narthex'

    def handle(self, *args, **options):

        start = datetime.now()
        self.stdout.write('Starting to loading EDM for orgId {}'.format(settings.ORG_ID))
        loader = NarthexBulkLoader()
        load_results = loader.walk_all_datasets()
        self.stdout.write("result bulkloading: {}".format(load_results))
        self.stdout.write('Finished to loading EDM for orgId {} in {} seconds.'.format(
            settings.ORG_ID,
            datetime.now() - start
        ))


