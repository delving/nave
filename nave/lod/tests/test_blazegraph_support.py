import pytest
import requests

from lod.utils import rdfstore

rdf_store = rdfstore.create_rdf_store(
    rdf_store_type="BlazeGraph",
    port="9999",
    host="http://localhost",
    db_name="brabantcloud_test",
)

try:
    response = requests.get(rdf_store.get_sparql_query_url + "?query=ask {?s ?p ?o}")
    blaze_graph_available = response.status_code == 200
except Exception:
    blaze_graph_available = False

def test__blazegraph__should_have_the_full_path_as_db():
    assert rdf_store.db.startswith("blazegraph/namespace/")
    assert rdf_store.graph_store_uri_suffix == "sparql"
    assert rdf_store.sparql_query_uri_suffix == "sparql"
    assert rdf_store.sparql_update_uri_suffix == "sparql"
    assert rdf_store.port == "9999"
    assert rdf_store.db.endswith("_test")


def test__blazegraph_sparql_query():
    if blaze_graph_available:
        response = rdf_store.query(query="select * {?s ?p ?o} limit 10")
        assert response is not None
        assert sorted(list(response.keys())) == ['head', 'results']

def test__blazegraph__should_be_able_to_insert_triples_via_update():
    if blaze_graph_available:
        query = """INSERT {GRAPH ?g {<urn:s> <urn:p> <urn:o>} }
        WHERE {
             BIND( IRI(CONCAT("urn:myNewGraph_",STR(NOW()))) as ?g )
        }"""
        assert rdf_store.update(query=query)


def test__blazegraph__should_be_able_to_query_triples():
    if blaze_graph_available:
        assert rdf_store.ask(query="where {<urn:s> <urn:p> <urn:o>}")


@pytest.mark.skip()
def test__blazegraph__should_support_graph_store_protocol():
    if blaze_graph_available:
        n_triples = "<urn:s1> <urn:p2> <urn:o2> ."
        graph_store = rdf_store.get_graph_store
        assert graph_store.post(named_graph="urn:g2", data=n_triples)
