# -*- coding: utf-8 -*-
"""This module test the EDM mapping type.


"""
from unittest import skip

from django.test import TestCase
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import FOAF, DC

from nave.lod.utils.resolver import RDFPredicate, RDFObject, RDFResource, GraphBindings


test_data = """<?xml version='1.0' encoding='utf-8'?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:ore="http://www.openarchives.org/ore/terms/"
        xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:owl="http://www.w3.org/2002/07/owl#"
        xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:edm="http://www.europeana.eu/schemas/edm/"
        xmlns:nave="http://schemas.delving.eu/nave/terms/" xmlns:narthex="http://schemas.delving.eu/narthex/terms/">
        <skos:Concept rdf:about="http://data.beeldengeluid.nl/gtaa/155912">
            <skos:prefLabel xml:lang="nl">Steger, E.A.M.A.</skos:prefLabel>
            <skos:definition>A person</skos:definition>
        </skos:Concept>
        <edm:ProvidedCHO rdf:about="http://www.openbeelden.nl/files/01/65/165083.WEEKNUMMER552-HRE0000CF2E.mpg">
          <dc:subject xml:lang="nl">
            <rdf:Description rdf:about="http://data.beeldengeluid.nl/gtaa/26980">
              <skos:prefLabel xml:lang="nl">tweelingen</skos:prefLabel>
            </rdf:Description>
          </dc:subject>
          <dc:subject xml:lang="nl">
            <narthex:ProxyResource rdf:about="http://data.beeldengeluid.nl/gtaa/enrichment_link">
              <narthex:proxyLiteralValue xml:lang="nl">test enriched</narthex:proxyLiteralValue>
            </narthex:ProxyResource>
          </dc:subject>
           <dc:subject rdf:resource="http://data.beeldengeluid.nl/gtaa/155912"/>
          <dc:subject xml:lang="nl">
            <narthex:ProxyResource rdf:about="http://data.beeldengeluid.nl/gtaa/155912_enriched">
              <narthex:proxyLiteralValue xml:lang="nl">Steger, Emmy</narthex:proxyLiteralValue>
              <skos:exactMatch rdf:resource="http://data.beeldengeluid.nl/gtaa/155912"/>
            </narthex:ProxyResource>
          </dc:subject>
          <dc:contributor>
            <rdf:Description rdf:about="http://data.beeldengeluid.nl/gtaa/182523">
              <skos:prefLabel xml:lang="nl">Bloemendal, Philip</skos:prefLabel>
            </rdf:Description>
          </dc:contributor>
          <dc:title xml:lang="nl">Het Europees tweelingencongres in Oirschot</dc:title>
          <dc:creator xml:lang="en">Polygoon-Profilti (producer) / Netherlands Institute for Sound and Vision (curator)</dc:creator>
          <dc:description xml:lang="nl">Bioscoopjournaals waarin Nederlandse onderwerpen van een bepaalde week worden gepresenteerd.</dc:description>
          <dc:description xml:lang="nl">Europees tweelingencongres te Oirschot, met 300 tweelingparen, met oa de tweelingbroers Lipman uit Huissen, Bartels en Kiehl uit West-Duitsland, de zussen Bernadette en Renee Smits uit Boxtel en Nellie en Ali Zondevan uit Marken, Kees en Trees van Iersel uit Tilburg en E.A.M.A. Steger, burgemeester van Oirschot. Er wordt een Brabantse koffiemaaltijd geserveerd, waarna op de markt een prijsuitreiking plaatsvindt, waarbij de broers Beers uit Tilburg en de zussen Sigrid en Karin Grandel uit Finland prijzen winnen en de zussen Diepvens uit België tot Europa-tweeling 1955 worden uitgeroepen.</dc:description>
          <dc:subject xml:lang="en">twins</dc:subject>
          <dc:subject xml:lang="en">Steger, E.A.M.A.</dc:subject>
          <dc:date>1955-05-22</dc:date>
          <dc:title xml:lang="en">The European twin congress in Oirschot</dc:title>
          <dc:source xml:lang="nl">WEEKNUMMER552-HRE0000CF2E</dc:source>
          <dc:language>nl</dc:language>
          <dc:type>Moving Image</dc:type>
          <dc:creator xml:lang="nl">Polygoon-Profilti (producent) / Nederlands Instituut voor Beeld en Geluid (beheerder)</dc:creator>
          <dc:description xml:lang="en">Newsreels in which Dutch subjects of a certain week are presented.</dc:description>
          <dc:description xml:lang="en">European twin congress in Oirschot, with 300 twin couples. Present are a.o. the twin brothers Lipman from Huissen, Bartels and Kiehl from West Germany, the sisters Bernadette and Renee Smits from Boxtel and Nellie and Ali Zondevan from Marken, Kees and Trees van Iersel from Tilburg and E.A.M.A. Steger, mayor of Oirschot. A Brabant coffee meal is served, after which the award ceremony takes place. The borthers Beers from Tilburg and the sisters Sigrid and Karin Grandel from Finland win prizes and the sisters Diepvens from Belgium are declared Europe twins of 1955.</dc:description>
          <dc:publisher xml:lang="nl">Nederlands Instituut voor Beeld en Geluid</dc:publisher>
          <dc:identifier>524834</dc:identifier>
          <dcterms:alternative xml:lang="en">Week number 55-22</dcterms:alternative>
          <dcterms:alternative xml:lang="nl">Weeknummer 55-22</dcterms:alternative>
          <dcterms:spatial xml:lang="en">Netherlands</dcterms:spatial>
          <dcterms:spatial xml:lang="en">Oirschot</dcterms:spatial>
          <dcterms:spatial xml:lang="nl">
            <rdf:Description rdf:about="http://data.beeldengeluid.nl/gtaa/39742">
              <skos:prefLabel xml:lang="nl">Nederland</skos:prefLabel>
              <geo:lat rdf:datatype="http://www.w3.org/2001/XMLSchema#double">52.13263</geo:lat>
              <geo:long rdf:datatype="http://www.w3.org/2001/XMLSchema#double">5.29127</geo:long>
            </rdf:Description>
          </dcterms:spatial>
          <dcterms:spatial xml:lang="nl">
            <rdf:Description rdf:about="http://data.beeldengeluid.nl/gtaa/40238">
              <skos:prefLabel xml:lang="nl">Oirschot</skos:prefLabel>
              <geo:lat rdf:datatype="http://www.w3.org/2001/XMLSchema#double">51.50705</geo:lat>
              <geo:long rdf:datatype="http://www.w3.org/2001/XMLSchema#double">5.30918</geo:long>
            </rdf:Description>
          </dcterms:spatial>
          <dcterms:extent>PT1M36S</dcterms:extent>
          <dcterms:medium>film</dcterms:medium>
          <edm:type>VIDEO</edm:type>
        </edm:ProvidedCHO>
        <ore:Aggregation rdf:about="http://data.digitalecollectie.nl/ore/aggregation/http%3A%2F%2Fwww.openbeelden.nl%2Ffiles%2F01%2F65%2F165083.WEEKNUMMER552-HRE0000CF2E.mpg">
          <edm:aggregatedCHO rdf:resource="http://www.openbeelden.nl/files/01/65/165083.WEEKNUMMER552-HRE0000CF2E.mpg"/>
          <edm:dataProvider>Open Beelden</edm:dataProvider>
          <edm:isShownAt>http://www.openbeelden.nl/media/165084</edm:isShownAt>
          <edm:isShownBy>http://www.openbeelden.nl/files/01/65/165083.WEEKNUMMER552-HRE0000CF2E.mpg</edm:isShownBy>
          <edm:object>http://www.openbeelden.nl/images/170053/Het_Europees_tweelingencongres_in_Oirschot_%280_48%29.png</edm:object>
          <edm:provider>Digitale Collectie</edm:provider>
          <edm:rights>http://creativecommons.org/licenses/by-sa/3.0/nl/</edm:rights>
        </ore:Aggregation>
        <nave:DcnResource>
            <nave:location>Berg en Dal</nave:location>
            <nave:province>Gelderland</nave:province>
        </nave:DcnResource>
      </rdf:RDF>
"""


class TestRDFPredicate(TestCase):
    """
    Test for the RDFPredicate object that is used in the views
    """

    def test_qname_conversion(self):
        uri = 'http://purl.org/dc/elements/1.1/title'
        predicate = RDFPredicate(uri)
        assert predicate.label == 'title'
        assert predicate.ns == 'http://purl.org/dc/elements/1.1/'
        assert predicate.prefix == "dc"
        assert predicate.search_label == "dc_title"
        assert predicate.qname == "dc:title"

    @skip
    def test_creation_with_unknown_ns(self):
        uri = 'http://localhost:8000/resource/aggregation/ton-smits-huis/454'
        predicate = RDFPredicate(uri)
        graph = Graph()
        graph.add((URIRef(uri), FOAF.name, Literal("sjoerd")))
        subject = list(graph.subjects())[0]
        uri_ref = URIRef(uri)
        assert uri_ref.n3() == "ns1:454"
        assert predicate is not None
        assert predicate.label is not None


class TestRDFObject(TestCase):
    """
    Test the RDFObject that is used in the views.
    """
    graph = Graph()
    graph.parse(data=test_data)
    bindings = GraphBindings(
        about_uri=URIRef(
            "http://data.digitalecollectie.nl/ore/aggregation/http%3A%2F%2Fwww.openbeelden.nl%2Ffiles%2F01%2F65%2F165083.WEEKNUMMER552-HRE0000CF2E.mpg"),
        graph=graph
    )

    def test_rdf_uri_ref_object(self):
        predicate = RDFPredicate('http://purl.org/dc/elements/1.1/creator')
        sorted_list = sorted(list(self.graph.objects(predicate=URIRef('http://purl.org/dc/elements/1.1/subject'))))
        test_obj = sorted_list[0]
        rdf_object = RDFObject(rdf_object=test_obj, graph=self.graph, predicate=predicate, bindings=self.bindings)
        assert rdf_object.is_uri
        assert not rdf_object.is_bnode
        assert not rdf_object.is_literal
        assert rdf_object.id == 'http://data.beeldengeluid.nl/gtaa/155912'
        assert str(rdf_object.value) == 'Steger, E.A.M.A.'
        assert rdf_object.value == Literal('Steger, E.A.M.A.', lang='nl')
        assert rdf_object.has_resource
        assert rdf_object.language == 'nl'
        assert rdf_object.object_type == 'URIRef'
        assert rdf_object.to_index_entry() == {
            '@type': 'URIRef',
            'value': 'Steger, E.A.M.A.',
            'raw': 'Steger, E.A.M.A.',
            'id': 'http://data.beeldengeluid.nl/gtaa/155912',
            'lang': 'nl',
            'inline': {
                'rdf_type': [{'@type': 'URIRef',
                              'id': 'http://www.w3.org/2004/02/skos/core#Concept',
                              'raw': 'skos:Concept',
                              'value': 'skos:Concept'}],
                'skos_definition': [{'@type': 'Literal',
                                    'raw': 'A person',
                                    'value': 'A person'}],
                'skos_prefLabel': [{'@type': 'Literal',
                                    'lang': 'nl',
                                    'raw': 'Steger, E.A.M.A.',
                                    'value': 'Steger, E.A.M.A.'}]
            }
        }
        assert rdf_object.resource_is_concept
        assert rdf_object.resource_has_skos_definition
        # second time the same should be True
        assert rdf_object.resource_is_concept
        assert rdf_object.resource_has_skos_definition

    def test_rdf_literal_object(self):
        predicate = RDFPredicate('http://purl.org/dc/elements/1.1/creator')
        sorted_list = sorted(list(self.graph.objects(predicate=URIRef('http://purl.org/dc/elements/1.1/subject'))))
        test_obj = sorted_list[-1]
        rdf_object = RDFObject(rdf_object=test_obj, graph=self.graph, predicate=predicate, bindings=self.bindings)
        assert not rdf_object.is_uri
        assert not rdf_object.is_bnode
        assert rdf_object.is_literal
        assert rdf_object.value == 'twins'
        assert not rdf_object.has_resource
        assert rdf_object.language == 'en'
        assert rdf_object.to_index_entry() == {
            '@type': 'Literal',
            'lang': 'en',
            'value': 'twins',
            'raw': 'twins',
        }
        assert not rdf_object.resource_is_concept


class TestRDFResource(TestCase):
    """
    Test the RDFResource that is used in the views
    """
    graph = Graph()
    graph.parse(data=test_data)
    bindings = GraphBindings(
        about_uri=URIRef(
            "http://data.digitalecollectie.nl/ore/aggregation/http%3A%2F%2Fwww.openbeelden.nl%2Ffiles%2F01%2F65%2F165083.WEEKNUMMER552-HRE0000CF2E.mpg"),
        graph=graph
    )

    def test_initial_create(self):
        test_uri = 'http://www.openbeelden.nl/files/01/65/165083.WEEKNUMMER552-HRE0000CF2E.mpg'
        resource = RDFResource(
            subject_uri=test_uri,
            graph=self.graph,
            bindings=self.bindings
        )
        assert resource.subject_uri == URIRef(test_uri)
        assert str(resource.get_type().uri) == 'http://www.europeana.eu/schemas/edm/ProvidedCHO'
        assert len(resource.get_predicates()) == 16
        assert len(resource.get_items()) == 16
        assert len(resource.get_objects()) == 30
        assert not resource.has_geo()

    def test_resource_to_index_doc(self):
        test_uri = 'http://www.openbeelden.nl/files/01/65/165083.WEEKNUMMER552-HRE0000CF2E.mpg'
        resource = RDFResource(
            subject_uri=test_uri,
            graph=self.graph,
            bindings=self.bindings
        )
        assert resource.subject_uri == URIRef(test_uri)
        index_doc = resource.to_index_entry()
        assert len(index_doc.keys()) > 0
        assert index_doc.get('dcterms_extent')[0]['value'] == 'PT1M36S'
        assert index_doc.get('dcterms_extent')[0]["@type"] == "Literal"
        assert len(index_doc.get('rdf_type')) > 0
        assert index_doc.get('rdf_type') == [
            {'@type': 'URIRef',
             'id': 'http://www.europeana.eu/schemas/edm/ProvidedCHO',
             'value': 'edm:ProvidedCHO',
             'raw': 'edm:ProvidedCHO',
             }
        ]


class TestGraphBindings(TestCase):
    """ Test the Graph Bindings module. """

    @classmethod
    def setUpClass(cls):
        cls.graph = Graph()
        cls.graph.parse(data=test_data)
        cls.about_uri = "http://data.digitalecollectie.nl/ore/aggregation/http%3A%2F%2Fwww.openbeelden.nl%2Ffiles%2F01%2F65%2F165083.WEEKNUMMER552-HRE0000CF2E.mpg"
        cls.bindings = GraphBindings(
            about_uri=cls.about_uri,
            graph=cls.graph,
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def test_graph_bindings(self):
        bindings = self.bindings
        assert bindings.about_uri() == URIRef(self.about_uri)
        assert len(bindings.get_available_resources_types) == 6
        assert len(bindings.get_resource_list) == 10
        mpg = 'http://www.openbeelden.nl/files/01/65/165083.WEEKNUMMER552-HRE0000CF2E.mpg'
        assert bindings.get_resource(mpg)
        assert len(bindings.get_resource(mpg).get_items()) == 16
        assert bindings.get_about_resource()
        assert len(bindings.get_about_resource().get_items()) == 8
        assert bindings.has_resource(URIRef('http://data.beeldengeluid.nl/gtaa/155912'))
        assert not bindings.has_resource(URIRef('http://data.beeldengeluid.nl/gtaa/155912_bla'))
        assert len(bindings.get_about_caption) == 2
        assert sorted(bindings.get_about_caption) == [
            Literal('The European twin congress in Oirschot', lang='en'),
            Literal('Het Europees tweelingencongres in Oirschot',
                    lang='nl')
        ]
        assert bindings.get_about_thumbnail is not None
        assert bindings.get_about_thumbnail == "http://www.openbeelden.nl/images/170053/Het_Europees_tweelingencongres_in_Oirschot_%280_48%29.png"

    def test_graph_bindings_to_index_doc(self):
        bindings = self.bindings
        index_doc = bindings.to_index_doc()
        assert index_doc is not None
        assert 'about' in index_doc
        about = index_doc['about']
        assert sorted(list(about.keys())) == ['caption', 'class', 'language', 'point', 'property', 'thumbnail']
        assert len(about['language']) == 2
        assert sorted([lang['raw'] for lang in about['language']]) == ['en', 'nl']
        assert about['property'] is not None
        assert len(about['property']) == 33
        prop_list = sorted([prop['raw'] for prop in about['property']])
        assert len(set(prop_list)) == 33
        assert 'dcterms:spatial' in prop_list
        assert about['class'] is not None
        assert len(about['class']) == 5
        class_list = sorted([prop['raw'] for prop in about['class']])
        assert len(class_list) == 5
        assert 'edm:ProvidedCHO' in class_list
        assert sorted(class_list) == sorted(['edm:ProvidedCHO', 'ore:Aggregation', 'skos:Concept', 'nave:DcnResource',
                                             'narthex:ProxyResource'])
        assert index_doc['rdf_type'][0]['value'] == "ore:Aggregation"
        assert 'inline' in index_doc['edm_aggregatedCHO'][0]
        assert len(about['caption']) == 2

    def test_graph_bindings_to_flat_index_doc(self):
        bindings = self.bindings
        index_doc = bindings.to_flat_index_doc()
        assert index_doc is not None
        subjects = index_doc['dc_subject']
        assert subjects is not None
        assert len(subjects) == 6
        ids = [subject['id'] for subject in subjects if subject['@type'] == 'URIRef']
        assert len(ids) == 3
        assert not 'http://data.beeldengeluid.nl/gtaa/enrichment_link' in ids
        literals = [subject['value'] for subject in subjects if subject['@type'] == 'Literal']
        assert len(literals) == 3

    @skip
    def test_for_enrichment_skos_entry(self):
        entries = list(self.graph.subject_objects(predicate=DC.subject))
        assert entries is not None
        assert len(entries) == 6
        enrichment_link = 'http://data.beeldengeluid.nl/gtaa/enrichment_link'
        rdf_resource = RDFResource(
            subject_uri=enrichment_link,
            graph=self.graph,
            bindings=self.bindings
        )
        # unlinked entry
        enrichment, linked = rdf_resource.is_enrichment()
        assert linked is not None
        assert isinstance(linked, bool)
        assert not linked

        linked_enrichment_link = "http://data.beeldengeluid.nl/gtaa/155912_enriched"
        rdf_resource = RDFResource(
            subject_uri=linked_enrichment_link,
            graph=self.graph,
            bindings=self.bindings
        )
        assert rdf_resource.is_enrichment() is not None
        # should be linked
        enrichment, islinked = rdf_resource.is_enrichment()
        assert enrichment
        assert islinked

        linked_enrichment_link = "http://data.beeldengeluid.nl/gtaa/155912"
        rdf_resource = RDFResource(
            subject_uri=linked_enrichment_link,
            graph=self.graph,
            bindings=self.bindings
        )
        # not enrichment not linked
        assert rdf_resource.is_enrichment() is not None
        enrichment, islinked = rdf_resource.is_enrichment()
        assert not islinked
        assert not enrichment

        #
        rdf_object = RDFObject(
            URIRef('%s' % enrichment_link),
            graph=self.graph,
            predicate=DC.subject,
            bindings=self.bindings
        )
        assert not rdf_object.is_uri
        assert rdf_object.id != enrichment_link
        assert not rdf_object.has_resource
        assert rdf_object.is_literal
        assert rdf_object.id is None
        assert rdf_object.value == "test enriched"
        assert rdf_object._is_normalised
        assert not rdf_object._is_inlined

        rdf_object = RDFObject(
            URIRef('%s' % "http://data.beeldengeluid.nl/gtaa/155912_enriched"),
            graph=self.graph,
            predicate=DC.subject,
            bindings=self.bindings
        )
        assert rdf_object.is_uri
        # assert not rdf_object.has_resource
        assert rdf_object.id is not None
        assert rdf_object.id == "http://data.beeldengeluid.nl/gtaa/155912"
        assert str(rdf_object.value) == "Steger, E.A.M.A."
        assert rdf_object._is_inlined
        assert not rdf_object._is_normalised






