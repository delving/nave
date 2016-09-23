# -*- coding: utf-8 -*-
"""This module does


"""
from unittest import TestCase
import time

from django.conf import settings
from elasticsearch import helpers
from elasticsearch_dsl import Search


es_action = {'_index': 'nested_test', '_id': 'dcn_cache_http%3A//nl.dbpedia.org/resource/Ton_Smits#cached',
             'rdfs_isDefinedBy': [
                 {'raw': 'http://nl.dbpedia.org/resource/Ton_Smits#about',
                  'value': 'http://nl.dbpedia.org/resource/Ton_Smits#about',
                  '@type': 'URIRef',
                  'inline': {'cc_attributionName': [{'raw': 'cache', 'value': 'cache', '@type': 'Literal'}],
                             'cc_license': [{'raw': 'http://creativecommons.org/licenses/by/3.0/',
                                             'value': 'http://creativecommons.org/licenses/by/3.0/',
                                             '@type': 'URIRef',
                                             'id': 'http://creativecommons.org/licenses/by/3.0/'}],
                             'dct_created': [{'raw': '2015-03-16 20:12:38.986675+00:00',
                                              'value': '2015-03-16 20:12:38.986675+00:00',
                                              '@type': 'Literal'}],
                             'dct_modified': [{'raw': '2015-03-16 20:12:38.988993+00:00',
                                               'value': '2015-03-16 20:12:38.988993+00:00',
                                               '@type': 'Literal'}],
                             'cc_attributionURL': [{'raw': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                    'value': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                    '@type': 'URIRef',
                                                    'id': 'http://nl.dbpedia.org/resource/Ton_Smits'}],
                             'rdf_type': [
                                 {'raw': 'foaf:Document', 'value': 'foaf:Document', '@type': 'URIRef',
                                  'id': 'http://xmlns.com/foaf/0.1/Document'}], 'foaf_primaryTopic': [
                      {'raw': 'http://nl.dbpedia.org/resource/Ton_Smits',
                       'value': 'http://nl.dbpedia.org/resource/Ton_Smits',
                       '@type': 'URIRef',
                       'id': 'http://nl.dbpedia.org/resource/Ton_Smits'}]},
                  'id': 'http://nl.dbpedia.org/resource/Ton_Smits#about'}], 'about': {
    'class': [
        {'raw': 'foaf:Document', 'value': 'foaf:Document', '@type': 'URIRef',
         'id': 'http://xmlns.com/foaf/0.1/Document'},
        {'raw': 'lod:Cached', 'value': 'lod:Cached', '@type': 'URIRef',
         'id': 'http://http://localhost:8000/resource/ns/lod/Cached'}], 'thumbnail': [], 'language': [], 'property': [
    {'raw': 'cc:attributionName', 'value': 'cc:attributionName', '@type': 'URIRef',
     'id': 'http://creativecommons.org/ns#attributionName'}, {'raw': 'rdf:type', 'value': 'rdf:type', '@type': 'URIRef',
                                                              'id': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'},
    {'raw': 'cc:attributionURL', 'value': 'cc:attributionURL', '@type': 'URIRef',
     'id': 'http://creativecommons.org/ns#attributionURL'},
    {'raw': 'dct:modified', 'value': 'dct:modified', '@type': 'URIRef', 'id': 'http://purl.org/dc/terms/modified'},
    {'raw': 'foaf:primaryTopic', 'value': 'foaf:primaryTopic', '@type': 'URIRef',
     'id': 'http://xmlns.com/foaf/0.1/primaryTopic'},
    {'raw': 'rdfs:isDefinedBy', 'value': 'rdfs:isDefinedBy', '@type': 'URIRef',
     'id': 'http://www.w3.org/2000/01/rdf-schema#isDefinedBy'},
    {'raw': 'dct:created', 'value': 'dct:created', '@type': 'URIRef', 'id': 'http://purl.org/dc/terms/created'},
    {'raw': 'cc:license', 'value': 'cc:license', '@type': 'URIRef', 'id': 'http://creativecommons.org/ns#license'}],
    'caption': [], 'point': []}, 'rdf_type': [{'raw': 'lod:Cached', 'value': 'lod:Cached', '@type': 'URIRef',
                                               'id': 'http://http://localhost:8000/resource/ns/lod/Cached'}],
             'system': {
                 'graph': '{\n  "@context": {\n    "abc": "http://www.ab-c.nl/",\n    "abm": "http://purl.org/abm/sen",\n    "abm1": "http://schemas.delving.eu/abm/",\n    "aff": "http://schemas.delving.eu/aff/",\n    "cc": "http://creativecommons.org/ns#",\n    "custom": "http://www.delving.eu/namespaces/custom",\n    "dbpedia-nl": "http://nl.dbpedia.org/resource/",\n    "dbpedia-owl": "http://dbpedia.org/ontology/",\n    "dc": "http://purl.org/dc/elements/1.1/",\n    "dct": "http://purl.org/dc/terms/",\n    "dcterms": "http://purl.org/dc/terms/",\n    "delving": "http://schemas.delving.eu/",\n    "devmode": "http://localhost:8000/resource/",\n    "drup": "http://www.itin.nl/drupal",\n    "edm": "http://www.europeana.eu/schemas/edm/",\n    "europeana": "http://www.europeana.eu/schemas/ese/",\n    "foaf": "http://xmlns.com/foaf/0.1/",\n    "gn": "http://www.geonames.org/ontology#",\n    "icn": "http://www.icn.nl/schemas/icn/",\n    "itin": "http://www.itin.nl/namespace",\n    "lod": "http://http://localhost:8000/resource/ns/lod/",\n    "musip": "http://www.musip.nl/",\n    "narthex": "http://schemas.delving.eu/narthex/terms/",\n    "nave": "http://schemas.delving.eu/nave/terms/",\n    "ore": "http://www.openarchives.org/ore/terms/",\n    "organisation": "http://localhost:8000/resource/organisation/",\n    "owl": "http://www.w3.org/2002/07/owl#",\n    "raw": "http://delving.eu/namespaces/raw",\n    "rce": "http://acc.lodd2.delving.org/rce/ns/",\n    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",\n    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",\n    "skos": "http://www.w3.org/2004/02/skos/core#",\n    "test": "http://http://localhost:8000/resource/ns/test/",\n    "tib": "http://www.tib.nl/schemas/tib/",\n    "tib1": "http://schemas.delving.eu/resource/ns/tib/",\n    "wgs84_pos": "http://www.w3.org/2003/01/geo/wgs84_pos#",\n    "xml": "http://www.w3.org/XML/1998/namespace",\n    "xsd": "http://www.w3.org/2001/XMLSchema#"\n  },\n  "@graph": [\n    {\n      "@id": "http://nl.dbpedia.org/resource/Ton_Smits#about",\n      "@type": "http://xmlns.com/foaf/0.1/Document",\n      "http://creativecommons.org/ns#attributionName": "cache",\n      "http://creativecommons.org/ns#attributionURL": {\n        "@id": "http://nl.dbpedia.org/resource/Ton_Smits"\n      },\n      "http://creativecommons.org/ns#license": {\n        "@id": "http://creativecommons.org/licenses/by/3.0/"\n      },\n      "http://purl.org/dc/terms/created": {\n        "@type": "xsd:date",\n        "@value": "2015-03-16T20:12:38.986675+00:00"\n      },\n      "http://purl.org/dc/terms/modified": {\n        "@type": "xsd:date",\n        "@value": "2015-03-16T20:12:38.988993+00:00"\n      },\n      "http://xmlns.com/foaf/0.1/primaryTopic": {\n        "@id": "http://nl.dbpedia.org/resource/Ton_Smits"\n      }\n    },\n    {\n      "@id": "http://nl.dbpedia.org/resource/Ton_Smits",\n      "@type": "http://http://localhost:8000/resource/ns/lod/Cached",\n      "http://www.w3.org/2000/01/rdf-schema#isDefinedBy": {\n        "@id": "http://nl.dbpedia.org/resource/Ton_Smits#about"\n      }\n    }\n  ],\n  "@id": "http://nl.dbpedia.org/resource/Ton_Smits#graph"\n}',
                 'delving_hubId': 'dcn_cache_http%3A//nl.dbpedia.org/resource/Ton_Smits#cached',
                 'slug': 'dcn_cache_http3anldbpediaorgresourceton_smitscached', 'delving_recordType': 'Cached',
                 'delving_spec': 'cache'}, '_op_type': 'index', '_type': 'lod_cacheresource'}

flat_es_action = {'_index': 'nested_test', '_source': {'thumbnail': [], 'property': [
    {'value': 'dct:created', 'raw': 'dct:created', 'id': 'http://purl.org/dc/terms/created', '@type': 'URIRef'},
    {'value': 'cc:license', 'raw': 'cc:license', 'id': 'http://creativecommons.org/ns#license', '@type': 'URIRef'},
    {'value': 'cc:attributionURL', 'raw': 'cc:attributionURL', 'id': 'http://creativecommons.org/ns#attributionURL',
     '@type': 'URIRef'},
    {'value': 'cc:attributionName', 'raw': 'cc:attributionName', 'id': 'http://creativecommons.org/ns#attributionName',
     '@type': 'URIRef'},
    {'value': 'rdfs:isDefinedBy', 'raw': 'rdfs:isDefinedBy', 'id': 'http://www.w3.org/2000/01/rdf-schema#isDefinedBy',
     '@type': 'URIRef'},
    {'value': 'rdf:type', 'raw': 'rdf:type', 'id': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
     '@type': 'URIRef'},
    {'value': 'dct:modified', 'raw': 'dct:modified', 'id': 'http://purl.org/dc/terms/modified', '@type': 'URIRef'},
    {'value': 'foaf:primaryTopic', 'raw': 'foaf:primaryTopic', 'id': 'http://xmlns.com/foaf/0.1/primaryTopic',
     '@type': 'URIRef'}], 'dct_created': [
    {'value': '2015-03-16 23:29:47.268122+00:00', 'raw': '2015-03-16 23:29:47.268122+00:00', '@type': 'Literal'}],
                                                 'cc_attributionURL': [
                                                     {'value': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                      'raw': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                      'id': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                      '@type': 'URIRef'}], 'cc_license': [
    {'value': 'http://creativecommons.org/licenses/by/3.0/', 'raw': 'http://creativecommons.org/licenses/by/3.0/',
     'id': 'http://creativecommons.org/licenses/by/3.0/', '@type': 'URIRef'}], 'point': [], 'class': [
    {'value': 'lod:Cached', 'raw': 'lod:Cached', 'id': 'http://http://localhost:8000/resource/ns/lod/Cached',
     '@type': 'URIRef'},
    {'value': 'foaf:Document', 'raw': 'foaf:Document', 'id': 'http://xmlns.com/foaf/0.1/Document', '@type': 'URIRef'}],
                                                 'cc_attributionName': [
                                                     {'value': 'cache', 'raw': 'cache', '@type': 'Literal'}],
                                                 'caption': [], 'language': [], 'rdf_type': [
    {'value': 'http://xmlns.com/foaf/0.1/Document', 'raw': 'http://xmlns.com/foaf/0.1/Document',
     'id': 'http://xmlns.com/foaf/0.1/Document', '@type': 'URIRef'},
    {'value': 'http://http://localhost:8000/resource/ns/lod/Cached',
     'raw': 'http://http://localhost:8000/resource/ns/lod/Cached',
     'id': 'http://http://localhost:8000/resource/ns/lod/Cached', '@type': 'URIRef'}], 'rdfs_isDefinedBy': [
    {'value': 'http://nl.dbpedia.org/resource/Ton_Smits#about', 'raw': 'http://nl.dbpedia.org/resource/Ton_Smits#about',
     'id': 'http://nl.dbpedia.org/resource/Ton_Smits#about', '@type': 'URIRef'}], 'dct_modified': [
    {'value': '2015-03-16 23:29:47.270540+00:00', 'raw': '2015-03-16 23:29:47.270540+00:00', '@type': 'Literal'}],
                                                 'foaf_primaryTopic': [
                                                     {'value': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                      'raw': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                      'id': 'http://nl.dbpedia.org/resource/Ton_Smits',
                                                      '@type': 'URIRef'}], 'system': {
    'slug': 'dcn_cache_http3anldbpediaorgresourceton_smitscached', 'delving_recordType': 'Cached',
    'delving_spec': 'cache', 'delving_hubId': 'dcn_cache_http%3A//nl.dbpedia.org/resource/Ton_Smits#cached'}},
                  '_op_type': 'index', '_id': 'dcn_cache_http%3A//nl.dbpedia.org/resource/Ton_Smits#cached',
                  '_type': 'lod_cacheresource'}


mappings = {
    "mappings": {
        "_default_":
            {
                "_all": {
                    "enabled": True
                },
                'properties': {
                    'id': {'type': 'integer'},
                    'absolute_url': {'type': 'string'},
                    "point": {
                        "type": "geo_point"
                    },
                    "delving_geohash": {
                        "type": "geo_point"
                    },
                    "rdf_type": {
                        "type": "nested"
                    }
                },
                "dynamic_templates": [
                    {"uri": {
                        "match": "id",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }},
                    {"point": {
                        "match": "point",
                        "mapping": {
                            "type": "geo_point",
                        }
                    }},
                    {"geo_hash": {
                        "match": "delving_geohash",
                        "mapping": {
                            "type": "geo_point",
                        }
                    }},
                    {"value": {
                        "match": "value",
                        "mapping": {
                            "type": "string",
                            "fields": {
                                "raw": {
                                    "type": "string",
                                    "index": "not_analyzed"
                                }
                            }
                        }
                    }},
                    {"raw": {
                        "match": "raw",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }},
                    {"id": {
                        "match": "id",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }},
                    {"inline": {
                        "match": "inline",
                        "mapping": {
                            "type": "object",
                            "include_in_parent": True,
                        }
                    }},
                    # {"property": {
                    #     "match": ".*_*",
                    #     "mapping": {
                    #         "type": "object",
                    #         "include_in_parent": True,
                    #     }
                    # }},
                ],
            }}}


class TestGraphIndexing(TestCase):
    """This class tests how nested graph indexing and searching works."""

    @classmethod
    def setUpClass(cls):
        from search import get_es_client
        cls.client = get_es_client()
        cls.index = "nested_test"
        if cls.client.indices.exists(cls.index):
            cls.client.indices.delete(cls.index)
        cls.client.indices.create(index=cls.index, body=mappings)
        cls.s = Search(using=cls.client, index=cls.index)
        # nr_indexed, errors = helpers.bulk(cls.client, actions=[es_action])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_bulk_index_actions(self):
        nr_indexed, errors = helpers.bulk(self.client, actions=[flat_es_action])
        assert errors == []
        assert nr_indexed == 1
        time.sleep(2)
        response = self.s.execute()
        assert response is not None
        assert response.hits.total == 1
        search_all_response = self.s.query("match", _all="URIRef").execute()
        assert search_all_response.hits.total == 1

        search_path_query = self.s.query("match",  **{"property.value.raw": "dct:created"})
        search_path_query.aggs.bucket('properties', 'terms', field='property.raw')
        search_path_response = search_path_query.execute()
        assert search_path_response.hits.total == 1
        assert search_path_response.aggregations.properties.buckets != []



