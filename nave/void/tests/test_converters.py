# -*- coding: utf-8 -*- 
"""This module test the graph to legacy format convertors

"""
from unittest import TestCase, skip

import pytest
from rdflib import URIRef, ConjunctiveGraph

from nave.lod.utils import rdfstore
from nave.void.convertors import TIBConverter, ICNConverter, DefaultAPIV2Converter, EDMStrictConverter
from nave.void.tests.test_es_result_fields import es_fields
from nave.void.tests.test_tasks import load_nquad_fixtures

legacy_output = {
    "dc_creator": ["Ton Smits"],
    "dc_description": [
        "Een vrouw ligt in een hangmat met naakt bovenlijf en en rok aan van bladeren. In haar hand een bloem. In de verte staat een kunstschilder achter een schildersezel en er staat een paard."],
    "dc_identifier": ["454"],
    "dc_rights": ["© L. Smits-Zoetmulder, info@tonsmitshuis.nl"],
    "dc_subject": ["bomen", "paarden", "kunstschilder", "atelier-ezels", "hangmatten", "vrouwen"],
    "dc_title": ["Zonder titel."],
    "dcterms_rightsHolder": ["© L. Smits-Zoetmulder, info@tonsmitshuis.nl"],
    "delving_allSchemas": ["tib_1.0.3"],
    "delving_collection": ["Ton Smits Huis"],
    "delving_creator": ["Ton Smits"],
    "delving_currentSchema": ["tib"],
    "delving_deepZoomUrl": [
        "http://media.delving.org/iip/deepzoom/mnt/tib/tiles/brabantcloud/ton-smits-huis/454.tif.dzi"],
    "delving_description": [
        "Een vrouw ligt in een hangmat met naakt bovenlijf en en rok aan van bladeren. In haar hand een bloem. In de verte staat een kunstschilder achter een schildersezel en er staat een paard."],
    "delving_hasDigitalObject": ["true"],
    "delving_hasGeoHash": ["false"],
    "delving_hasLandingPage": ["true"],
    "delving_hubId": ["brabantcloud_ton-smits-huis_454"],
    "delving_imageUrl": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500"],
    "delving_landingPage": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500"],
    "delving_orgId": ["brabantcloud"],
    "delving_owner": ["Ton Smits Huis"],
    "delving_pmhId": ["brabantcloud_ton-smits-huis_454"],
    "delving_provider": ["Erfgoed Brabant"],
    "delving_recordType": ["mdr"],
    "delving_spec": ["ton-smits-huis"],
    "delving_thumbnail": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/180"],
    "delving_title": ["Zonder titel."],
    "delving_visibility": ["10"],
    "europeana_collectionName": ["ton-smits-huis"],
    "europeana_collectionTitle": ["Ton Smits Huis"],
    "europeana_country": ["Netherlands"],
    "europeana_dataProvider": ["Ton Smits Huis"],
    "europeana_isShownAt": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500"],
    "europeana_isShownBy": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500"],
    "europeana_language": ["nl"],
    "europeana_object": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/180"],
    "europeana_provider": ["Erfgoed Brabant"],
    "europeana_rights": ["http://www.europeana.eu/rights/rr-r/"],
    "europeana_type": ["IMAGE"],
    "europeana_uri": ["ton-smits-huis/31313"],
    "tib_citName": ["ccBrabant_TSH"],
    "tib_citOldId": ["ccBrabant_TSH_454"],
    "tib_collection": ["Ton Smits Huis"],
    "tib_creatorRole": ["kunstschilder"],
    "tib_dimension": ["hoogte : 60 cm ", "breedte : 80 cm "],
    "tib_material": ["doek", "olieverf"],
    "tib_objectNumber": ["454"],
    "tib_objectSoort": ["schilderij"],
    "tib_place": ["Eindhoven"],
    "tib_productionEnd": ["1973"],
    "tib_productionPeriod": ["1973"],
    "tib_productionStart": ["1973"],
    "tib_technique": ["geschilderd"],
    "tib_thumbLarge": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/500"],
    "tib_thumbSmall": ["http://media.delving.org/thumbnail/brabantcloud/ton-smits-huis/454/180"]
}


@pytest.mark.django_db
@pytest.mark.usefixtures("settings")
class TestTIBConvertor(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.store = rdfstore._rdfstore_test
        cls.store._clear_all()
        cls.graph = load_nquad_fixtures()
        cls.dataset_graph_uri = "http://localhost:8000/resource/dataset/ton-smits-huis/graph"
        cls.about_uri = "http://localhost:8000/resource/aggregation/ton-smits-huis/454"

    @classmethod
    def tearDownClass(cls):
        cls.store._clear_all()

    def test_bindings(self):
        converter = TIBConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        assert converter.bindings() is not None
        output = converter.convert()
        assert output is not None
        assert len(output.keys()) > 0
        assert output.get('delving_hasDigitalObject')
        assert 'europeana_uri' in output
        assert 'europeana_isShownAt' in output
        assert '/' in output.get('europeana_uri')[0]
        assert 'Smits, Ton' in output.get('dc_creator')

    def test_edm_strict(self):
        converter = EDMStrictConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        assert converter
        assert converter.graph
        output = converter.convert(output_format='xml')
        assert output
        assert 'datasetRecordCount' not in output
        assert 'nave:location' not in output

    def test_with_es_fields(self):
        converter = ICNConverter(
            es_result_fields=es_fields
        )
        assert converter._es_result_fields is not None
        output = converter.convert()
        assert output is not None
        assert len(output.keys()) > 0
        assert output.get('delving_hasDigitalObject')

    def test_with_default_v2_converter(self):
        converter = DefaultAPIV2Converter(
            es_result_fields=es_fields
        )
        assert converter
        assert converter.bindings() is None
        assert converter._es_result_fields is not None
        output = converter.convert()
        assert output
        assert 'graph' not in output
        assert 'rdf' not in output
        assert not any([k.startswith('narthex_')for k in output.keys()])
        edm_isShownBy = output.get('edm_isShownBy')
        assert edm_isShownBy
        assert len(edm_isShownBy) == 1
        assert 'raw' not in edm_isShownBy[0]

    def test_get_inline_links(self):
        converter = TIBConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        links = converter._get_inline_links()
        assert links is not None
        assert isinstance(links, dict)
        assert len(links) == 1

    def test_get_inline_preview(self):
        converter = TIBConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        previews = converter._get_inline_preview(link=self.about_uri, store=self.store)
        assert previews is not None
        assert 'delving_hubId' in previews
        assert previews['delving_hubId'] == "brabantcloud_ton-smits-huis_454"
        assert len(previews) == 5

    def test_get_inline_dict(self):
        converter = TIBConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        assert converter is not None
        pred = URIRef('http://purl.org/dc/elements/1.1/identifier')
        links = {
            pred: [self.about_uri]
        }
        inline_dict = converter.get_inline_dict(
            links=links,
            store=self.store
        )
        assert inline_dict is not None
        assert isinstance(inline_dict, dict)
        assert len(inline_dict) > 0
        print(inline_dict)
        assert (pred, self.about_uri) in inline_dict
        assert isinstance(inline_dict[(pred, self.about_uri)], dict)

    @skip
    def test_update_graph_with_inlines(self):
        converter = TIBConverter(
            graph=self.graph,
            about_uri=self.about_uri
        )
        assert converter is not None
        pred = URIRef('http://purl.org/dc/elements/1.1/identifier')
        inline_dict = converter.get_inline_dict(
            links={
                pred: [self.about_uri]
            },
            store=self.store
        )
        target_inline_uri = self.about_uri.replace("454", "455")
        inline_dict[(pred, target_inline_uri)] = inline_dict[(pred, self.about_uri)]
        del inline_dict[(pred, self.about_uri)]
        converter._update_graph_with_inlines(inline_dict)
        graph = self.graph
        assert graph is not None
        assert isinstance(graph, ConjunctiveGraph)
        inlines = list(graph.objects(predicate=pred))
        assert len(inlines) == 1
        inline = str(inlines[0])
        assert inline != target_inline_uri
        assert isinstance(inline, str)
        assert "brabantcloud_ton-smits-huis_454" in inline

