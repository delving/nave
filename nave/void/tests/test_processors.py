import os

from django.test import override_settings
from rdflib import Literal, URIRef
from rdflib.namespace import DC

from nave.lod.utils import rdfstore
from nave.void.processors import BulkApiProcessor, IndexApiProcessor, \
     CUSTOM_NS, DELVING

INDEX_JSON = """{
    "indexRequest": {
        "indexItem": [
            {
            "@itemId": "2773",
            "@itemType": "image",
            "@delete": "false",
            "field": [
                {
                "@name": "dc:title",
                "@fieldType": "text",
                "#text": "test16"
                },
                {
                "@name": "dc:creator",
                "@fieldType": "text"
                },
                {
                "@name": "dc:subject",
                "@fieldType": "text"
                },
                {
                "@name": "icn:technique",
                "@fieldType": "text"
                },
                {
                "@name": "icn:material",
                "@fieldType": "text"
                },
                {
                "@name": "city",
                "@fieldType": "location",
                "#text": "52.0957251,4.3616082"
                },
                {
                "@name": "europeana_isShownAt",
                "@fieldType": "link",
                "#text": "urn:123/456"
                }
            ],
            "systemField": [
                {
                "@name": "owner",
                "#text": "Redactie Zeeuwse Ankers"
                },
                {
                "@name": "title",
                "#text": "test16"
                },
                {
                "@name": "thumbnail",
                "#text": "http://www.zeeuwseankers.nl/data/uploads/thumbnails/20170112175877b048178c8.jpg"
                },
                {
                "@name": "fullText"
                },
                {
                "@name": "landingPage",
                "#text": "http://www.zeeuwseankers.nl/data/uploads/20170112175877b048178c8.jpg"
                }
            ]
            },
            {
                "@itemId": "2774",
                "@itemType": "image",
                "@delete": "true"
            },
            {
                "@itemId": "2775",
                "@itemType": "image",
                "@delete": "false",
                "field": [
                {
                "@name": "dc:title",
                "@fieldType": "text",
                "#text": "test16"
                },
                {
                "@name": "dc:creator",
                "@fieldType": "text"
                },
                {
                "@name": "dc:subject",
                "@fieldType": "text"
                },
                {
                "@name": "icn:technique",
                "@fieldType": "text"
                },
                {
                "@name": "icn:material",
                "@fieldType": "text"
                }
            ],
            "systemField": [
                {
                "@name": "owner",
                "#text": "Redactie Zeeuwse Ankers"
                },
                {
                "@name": "title",
                "#text": "test16"
                },
                {
                "@name": "thumbnail",
                "#text": "http://www.zeeuwseankers.nl/data/uploads/thumbnails/20170112175877b048178c8.jpg"
                },
                {
                "@name": "fullText"
                },
                {
                "@name": "landingPage",
                "#text": "http://www.zeeuwseankers.nl/data/uploads/20170112175877b048178c8.jpg"
                }
            ]
            }
        ]
    }
}"""


def test__index_api__payload_should_validate_as_json():
    """Test if the payload is an object we can process."""
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    assert processor
    assert processor.validate() == (True, None)
    assert isinstance(processor.data, dict)


def test__index_api__get_status_from_item():
    """Extract deleted boolean from json item."""
    test_index = {
        "@itemId": "2773",
        "@itemType": "image",
        "@delete": "false",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    assert not processor.get_delete_status(test_index)
    test_delete = {
        "@itemId": "2773",
        "@itemType": "image",
        "@delete": "true",
    }
    assert processor.get_delete_status(test_delete)
    test_missing = {
        "@itemId": "2773",
        "@itemType": "image",
    }
    assert not processor.get_delete_status(test_missing)


def test__index_api__create_hub_id():
    """Test the creation of the hubId."""
    test_index = {
        "@itemId": "2773",
        "@itemType": "image",
        "@delete": "false",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    hub_id = processor.create_hub_id(test_index)
    assert hub_id
    assert len(hub_id.split('_')) == 3
    assert hub_id.endswith('_image_2773')


def test__index_api__get_spec():
    """Get spec from index item."""
    test_index = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "false",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    spec = processor.get_spec(test_index)
    assert spec
    assert spec == 'image'


def test__index_api__get_record_type():
    """Return the record type of the index Item"""
    test_index = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "false",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    record_type = processor.get_record_type(test_index)
    assert record_type
    assert record_type == "indexitem"


def test__index_api__get_doc_type():
    """Test for the correct doctype for the index item."""
    item = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "false",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    doc_type = processor.get_doc_type(item)
    assert doc_type
    assert doc_type == "indexitem"
    assert doc_type == processor.get_record_type(item)


def test__index_api__create_delete_action():
    """Test creation of Elasticsearch delete actions."""
    item = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "true",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    es_action = processor.create_delete_action(item)
    assert es_action
    assert es_action['_op_type'] == 'delete'
    assert es_action['_type'] == 'indexitem'
    assert es_action['_id'] == processor.create_hub_id(item)


def test__index_api__custom_namespace():
    """Test the costum namespace access."""
    from nave.void.processors import CUSTOM_NS, NAVE, DELVING
    from rdflib import Namespace
    assert CUSTOM_NS
    assert isinstance(CUSTOM_NS, Namespace)
    assert CUSTOM_NS == Namespace('http://www.delving.eu/namespaces/custom/')
    assert NAVE
    assert DELVING


def test_index_api__get_local_id():
    """Test extraction of local_id from index item."""
    item = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "true",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    local_id = processor.get_local_id(item)
    assert local_id


def test__index_api__get_source_uri():
    """Test creation of the source uri from index item."""
    item = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "true",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    source_uri = processor.get_source_uri(item)
    assert source_uri
    parts = source_uri.split('/')
    assert parts[-1] == item['@itemId']
    assert parts[-2] == item['@itemType'].lower()
    assert parts[-3] == 'indexitem'


def test__index_api__get_named_graph():
    """Test creation of the named graph from the index item."""
    item = {
        "@itemId": "2773",
        "@itemType": "Image",
        "@delete": "true",
    }
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    source_uri = processor.get_source_uri(item)
    named_graph = processor.get_named_graph(item)
    assert named_graph
    assert named_graph.startswith(source_uri)
    assert named_graph.endswith('/graph')


def test__index_api__get_index_items():
    """Test extracting the index items from the payload."""
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    index_items = processor.get_index_items()
    assert index_items
    assert len(index_items) == 3
    processor = IndexApiProcessor(payload='{}')
    assert not processor.get_index_items()
    processor = IndexApiProcessor(payload='{"indexRequest": {}}')
    assert not processor.get_index_items()


def test__index_api__process_field():
    """Test processing field dicts from an index item."""
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    field = {
        "@name": "dc:title",
        "@fieldType": "text",
        "#text": "test16"
    }
    response = processor.process_field(field)
    assert response
    assert len(response) == 1
    pred, obj = response[0]
    assert isinstance(pred, URIRef)
    assert isinstance(obj, Literal)
    field = {
        "@name": "dc:title",
        "@fieldType": "link",
        "#text": "urn:123/456"
    }
    response = processor.process_field(field)
    assert response
    assert len(response) == 1
    pred, obj = response[0]
    assert isinstance(pred, URIRef)
    assert isinstance(obj, URIRef)
    field = {
        "@name": "city",
        "@fieldType": "location",
        "#text": "52.0957251,4.3616082"
    }
    response = processor.process_field(field)
    assert response
    assert len(response) == 2
    pred, obj = response[0]
    assert isinstance(pred, URIRef)
    assert pred == DELVING.geoHash
    assert isinstance(obj, Literal)
    pred, obj = response[1]
    assert isinstance(pred, URIRef)
    assert pred == CUSTOM_NS.city
    assert isinstance(obj, Literal)
    field = {
        "@name": "city",
        "@fieldType": "location",
    }
    response = processor.process_field(field)
    assert not response
    field = {
        "@name": "owner",
        "#text": "delving"
    }
    response = processor.process_field(field, system_field=True)
    assert response
    assert len(response) == 1
    pred, obj = response[0]
    assert pred == DELVING.owner
    assert str(obj) == 'delving'
    assert isinstance(obj, Literal)


def test__index_api__get_graph():
    """Create graph from index item."""
    from rdflib import URIRef
    from rdflib.namespace import RDF
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    item = processor.get_index_items()[0]
    s = processor.get_source_uri(item, as_uri=True)
    assert isinstance(s, URIRef)
    g = processor.to_graph(item)
    assert g is not None
    rdf_type = list(g.objects(subject=s, predicate=RDF.type))
    assert rdf_type
    assert len(rdf_type) == 1
    assert rdf_type[0].endswith('IndexItem')
    predicates = set(list(g.predicates()))
    assert predicates
    assert DELVING.owner in predicates
    assert DELVING.geoHash in predicates
    assert DC.title in predicates
    objects = set(list(g.objects()))
    assert objects
    assert Literal('52.0957251,4.3616082') in objects
    assert URIRef('urn:123/456') in objects


def test__index_api__get_es_action():
    """Create Elasticsearch bulk action from index item."""
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    item = processor.get_index_items()[0]
    es_action = processor.get_es_action(item)
    assert es_action
    assert es_action['_id'] == processor.create_hub_id(item)
    assert es_action['_type'] == processor.get_doc_type(item)
    assert es_action['_op_type'] == 'index'
    assert '_source' in es_action
    record = es_action['_source']
    assert 'dc_title' in record
    assert 'custom_city' in record
    assert 'delving_geoHash' in record


def test__index_api__process():
    """Test full processing of payload."""
    payload = INDEX_JSON
    processor = IndexApiProcessor(payload=payload)
    result = processor.process(index=False)
    assert result
    assert len(result) == 5
    assert result['totalItemCount'] == 3
    assert result['indexedItemCount'] == 2
    assert result['deletedItemCount'] == 1
    assert result['invalidItemCount'] == 0
    assert not result['invalidItems']


@override_settings(
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_ALWAYS_EAGER=True,
    BROKER_BACKEND='memory')
def test__processors__bulk_call():
    with open(os.path.join(os.path.dirname(__file__), 'resources/bulk_api_sample.txt'), 'r') as f:
        processor = BulkApiProcessor(f, store=rdfstore._rdfstore_test)
        assert processor
