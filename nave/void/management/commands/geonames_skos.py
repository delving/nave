# -*- coding: utf-8 -*-
import zipfile

import os
import requests
from django.core.management.base import BaseCommand
from rdflib import URIRef, Graph, RDF
from rdflib.namespace import SKOS


class Command(BaseCommand):
    args = '<country_code> <geoname_country_uri> <path to the full rdf dump in txt format>'
    help = 'Extract skosified entries per country'

    @staticmethod
    def add_broader_narrower(s, g):
        admin2 = g.objects(subject=s, predicate=URIRef('http://www.geonames.org/ontology#parentADM2'))
        admin1 = g.objects(subject=s, predicate=URIRef('http://www.geonames.org/ontology#parentADM1'))
        country = g.objects(subject=s, predicate=URIRef('http://www.geonames.org/ontology#parentCountry'))
        parent_feature = g.objects(subject=s, predicate=URIRef('http://www.geonames.org/ontology#parentFeature'))

        broader = [parent_feature, admin2, admin1, country]
        broader_order = list()
        for entry in broader:
            for geonames_id in entry:
                if geonames_id not in broader_order:
                    broader_order.append(geonames_id)

        pairs = []
        for entry in broader_order:
            current_idx = broader_order.index(entry)
            if len(broader_order) > current_idx + 1:
                pairs.append((broader_order[current_idx], broader_order[current_idx + 1]))

        g.add((broader_order[0], SKOS.narrower, s))
        g.add((s, SKOS.broader, broader_order[0]))

        for child, parent in pairs:
            g.add((parent, SKOS.narrower, child))
            g.add((child, SKOS.broader, parent))

    def get_skos_geonames(self, country_code, country_uri, geonames_rdf_file, features=None):
        if features is None:
            features = ['http://www.geonames.org/ontology#A.ADM1', 'http://www.geonames.org/ontology#A.ADM2',
                        'http://www.geonames.org/ontology#P.PPL']

        if not isinstance(country_uri, URIRef):
            country_uri = URIRef(country_uri)

        geonames_lang = '/tmp/geonames_{}_rdf.txt'.format(country_code)
        geonames_muni_county = '/tmp/geonames_{}_fylke_kommune.txt'.format(country_code)

        g = Graph()

        # split file
        with zipfile.ZipFile(geonames_rdf_file, "r") as z:
            with z.open("all-geonames-rdf.txt", 'r') as f, open(geonames_lang, 'w') as output, open(geonames_muni_county,
                                                                                               'w') as filtered_output:
                for line in f:
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    if country_uri in line and line.startswith('<?xml '):
                        output.write(line)
                        if any([feature in line for feature in features]):
                            filtered_output.write(line)
                            g.parse(data=line)

        # skosify the entries in the graph
        for s, p, o in g:

            if p in [RDF.type]:
                g.add((s, RDF.type, SKOS.Concept))
            if p in [URIRef('http://www.geonames.org/ontology#name')]:
                g.add((s, SKOS.prefLabel, o))
            if p in [URIRef('http://www.geonames.org/ontology#alternateName')]:
                g.add((s, SKOS.altLabel, o))

        # add broader links
        for s in g.subjects():
            self.add_broader_narrower(s, g)

        output_fname = "/tmp/geonames_{}_skos.xml"
        g.serialize(output_fname.format(country_code), format="xml")

        self.stdout.write('Wrote skos for {} to {}'.format(country_code, output_fname))

        return g

    def handle(self, *args, **options):
        country_code = args[0]
        country_uri = args[1]
        rdf_file_path = args[2]

        if rdf_file_path == "download":
            download_path = "http://download.geonames.org/all-geonames-rdf.zip"
            rdf_file_path = "/tmp/all-geonames-rdf.zip"
            if not os.path.exists(rdf_file_path):
                self.stdout.write("start downloading Geonames RDF dump")
                r = requests.get(download_path)
                with open(rdf_file_path, "wb") as code:
                    code.write(r.content)

                self.stdout.write("finish downloading Geonames RDF dump")

        self.stdout.write('Starting to generated skos for {} ({})'.format(country_uri, country_code))

        self.get_skos_geonames(country_code, country_uri, rdf_file_path)

        self.stdout.write('Finished generated skos for {} ({})'.format(country_uri, country_code))
