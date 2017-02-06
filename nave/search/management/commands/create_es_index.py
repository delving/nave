# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<index_name> <alias name>'
    help = 'Extract skosified entries per country'

    def handle(self, *args, **options):
        index_name = args[0]
        alias = args[1] if len(args) > 1 else None

        self.stdout.write('Started creating index for {} with alias: {}'.format(index_name, alias))

        from nave.search import create_index
        create_index(
                index_name=index_name,
                aliases=alias
        )

        self.stdout.write('Finished creating index for {} with alias: {}'.format(index_name, alias))
