# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<base_url> <spec> <format>'
    help = 'bulk load xml files processed by Narthex'

    def handle(self, *args, **options):
        if len(args) != 3:
            return self.args
        base_url = args[0]
        spec = args[1]
        metadata_prefix = args[2]

        self.stdout.write('Starting harvesting for {} from '.format(spec, base_url))
        from void.oaipmh import OAIHarvester
        harvester = OAIHarvester(base_url=base_url)
        output_file = harvester.get_records_from_oai_pmh(set_spec=spec, metadata_prefix=metadata_prefix)
        self.stdout.write('Wrote output to {}'.format(output_file))
        self.stdout.write('Finished harvesting for {} from '.format(spec, base_url))


