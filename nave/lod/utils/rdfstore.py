# -*- coding: utf-8 -*- 
""" This module provides wrappers to SPARQL query types

By default it uses the settings from the settings.py, but if you instantiate SPARQL directly you can override
these settings

"""
import logging

import os
import requests
from SPARQLWrapper import SPARQLWrapper, GET, JSON, POST
from django.conf import settings
from django.http import Http404
from django.utils.log import getLogger
from rdflib import Graph

from nave.lod import RDF_STORE_DB, RDF_STORE_HOST, RDF_STORE_PORT, namespace_manager

logger = getLogger(__name__)

urllib3_logger = logging.getLogger('requests')
urllib3_logger.setLevel(logging.WARN)


class QueryType:
    def __init__(self):
        pass

    ask = "ASK {}"
    describe = "DESCRIBE <{}>"
    select = "SELECT {}"
    count = "SELECT (COUNT(*) AS ?count) {}"
    distinct = "SELECT DISTINCT {}"
    delete = "DELETE "
    remove_insert = """WITH  <{named_graph}>  DELETE {{ {remove}  }} INSERT {{ {insert} }} WHERE {{ {remove} }};"""
    free_text = "{}"


class RDFStore:
    """
    This class is a wrapper for all SPARQL queries supported by the LoD app
    """

    def __init__(self, db=RDF_STORE_DB, host=RDF_STORE_HOST, port=RDF_STORE_PORT, acceptance_mode=False,
                 graph_store_uri_suffix="data", sparql_query_uri_suffix="sparql",
                 sparql_update_uri_suffix="update", rdf_store_type=None, graph_store_graph_param="graph"
                 ):
        self.rdf_store_type = rdf_store_type
        self.db = db if not acceptance_mode else "{}_acceptance".format(db)
        self.host = host
        self.port = port
        self.acceptance_mode = acceptance_mode
        self.graph_store_uri_suffix = graph_store_uri_suffix
        self.graph_store_graph_param = graph_store_graph_param
        self.sparql_query_uri_suffix = sparql_query_uri_suffix
        self.sparql_update_uri_suffix = sparql_update_uri_suffix
        self.base_url = self.get_store_url
        self.namespace_manager = namespace_manager
        self.graph_store = None

    @property
    def get_store_url(self):
        store_type = getattr(settings, "RDF_STORE_TYPE", "Fuseki")
        if self.rdf_store_type is None and store_type:
            self.rdf_store_type = store_type
        if self.rdf_store_type.lower() == "blazegraph":
            rdf_url = "{}:{}/bigdata/namespace/{}".format(self.host, self.port, self.db)
            self.graph_store_uri_suffix = "sparql"
            self.sparql_query_uri_suffix = "sparql"
            self.sparql_update_uri_suffix = "sparql"
            self.graph_store_graph_param = "context-uri"
        else:
            rdf_url = "{}:{}/{}".format(self.host, self.port, self.db)
        return rdf_url

    @property
    def get_graph_store(self):
        """ Initialise and/or return GraphStore.

        :return: GraphStore
        """
        if not self.graph_store:
            self.graph_store = GraphStore(rdf_store=self)
        return self.graph_store

    # @retry(exceptions=TimeoutError, tries=2, jitter=(1000, 2000))
    def build_sparql_query(self, query, query_type, query_method=GET, named_graph=None, update=False):
        """Construct the boilerplate of a sparql query
        """
        sparql_uri = self.get_sparql_query_url if not update else self.get_sparql_update_url
        sparql = SPARQLWrapper(sparql_uri)
        sparql.setMethod(POST if update else query_method)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(15 if update else 10)
        if named_graph:
            sparql.addParameter("default-graph-uri", named_graph)
        if isinstance(query, dict):
            sparql.setQuery(query_type.format(**query))
        else:
            sparql.setQuery(query_type.format(query))
        response = sparql.queryAndConvert()
        return response

    @property
    def get_graph_store_url(self):
        """return the full URL to use the Graph Store Protocol."""
        return "{}/{}".format(self.base_url, self.graph_store_uri_suffix)

    @property
    def get_sparql_query_url(self):
        return "{}/{}".format(self.base_url, self.sparql_query_uri_suffix)

    @property
    def get_sparql_update_url(self):
        return "{}/{}".format(self.base_url, self.sparql_update_uri_suffix)

    def ask(self, uri=None, query="where {{?s ?p ?o}}", named_graph=None):
        """
        Create and execute an ASK SPARQL query

        :param uri:
        :param query:
        :type named_graph: string
        :return: Boolean
        """
        query = "where {{<{}> ?p ?o}}".format(uri) if uri else "{}".format(query)
        response = self.build_sparql_query(query, QueryType.ask, named_graph=named_graph)
        return response['boolean']

    def count(self, query="where {{?s ?p ?o}}", named_graph=None):
        """Create a count query.

        :return: int
        """
        response = self.build_sparql_query(query=query, query_type=QueryType.count, named_graph=named_graph)
        return int(response['results']['bindings'][0]['count']['value'])

    def describe(self, uri, named_graph=None):
        """
        create SPARQL describe query
        """
        graph = self.build_sparql_query(query=uri, query_type=QueryType.describe, named_graph=named_graph)
        graph.namespace_manager = get_namespace_manager()
        return graph

    def delete(self, query, named_graph=None):
        pass

    def remove_insert(self, remove, insert, named_graph=None):
        """Building a remove and insert SPARQL Query."""
        query = {'named_graph': named_graph, 'remove': remove, 'insert': insert}
        response = self.build_sparql_query(query=query,
                                           query_type=QueryType.remove_insert,
                                           named_graph=named_graph,
                                           update=True)
        logger.log(response)
        if "Update succeeded" in str(response):
            return True
        return False

    def select(self, query, named_graph=None, as_graph=False):
        """
        create SPARQL select query

        If you want to use the as_graph option you need to provide the following viables:
            ?s ?p ?o
            - or -
            ?s ?p ?o ?g

        These will be turned into triples or quads.

        """
        response = self.build_sparql_query(query=query, query_type=QueryType.select, named_graph=named_graph)
        if as_graph:
            # check three or four bindings
            # turn them into quads
            # load quads into graph
            # graph.namespace_manager = get_namespace_manager()
            graph = Graph(namespace_manager=namespace_manager)
            return graph
        return response

    def query(self, query):
        """
        create SPARQL select query

        If you want to use the as_graph option you need to provide the following viables:
            ?s ?p ?o
            - or -
            ?s ?p ?o ?g

        These will be turned into triples or quads.

        """
        response = self.build_sparql_query(query=query, query_type=QueryType.free_text)
        return response

    def update(self, query, named_graph=None):
        """Send an update query to the SPARQL update interface."""
        if not query:
            logger.warn("No SPARQL update query was given, so not sending the query to the triple-store.")
            return False
        response = self.build_sparql_query(query=query,
                                           query_type=QueryType.free_text,
                                           query_method=POST,
                                           named_graph=named_graph,
                                           update=True)
        if "Update succeeded" in str(response):
            return True
        return False

    def _clear_all(self):
        """ Clear all triples from the RDF store

        Use with great caution. It has been included for testing purposes.
        """
        return self.update(query="CLEAR ALL")

    def get_cached_source_uri(self, uri):
        query = """select distinct ?s where {{?s <http://schemas.delving.org/nave/terms/cacheUrl> <{}> }}
        """.format(uri)
        response = self.query(query)
        uris = [binding['s']['value'] for binding in response['results']['bindings']]
        if uris:
            return uris[0]
        return None


class UnknownGraph(Http404):
    """ Exception raised when the graph requested is unknown.
    """
    pass


class GraphStore:
    """
    This class deals with all the methods of the Graph Store protocol, see
    http://www.w3.org/TR/sparql11-http-rdf-update/
    """

    def __init__(self, rdf_store=RDFStore()):
        self.rdf_store = rdf_store
        self.graph_store = rdf_store.get_graph_store_url

    @staticmethod
    def _get_data_as_rdf_string(data):
        """Convert graphs or strings to the right format for a HTTP Request."""
        rdf_string = None
        if isinstance(data, Graph):
            rdf_string = data.serialize(encoding='utf-8', format='nt')
        elif isinstance(data, str):
            rdf_string = data
        else:
            raise ValueError("Unsupported data type for this operation: {}".format(type(data)))
        return rdf_string

    def delete(self, named_graph):
        """ Delete the named graph from the RDF store
        """
        response = requests.delete("{graph_store_url}?{graph_param}={graph_name_uri}".format(
            graph_store_url=self.graph_store,
            graph_param=self.rdf_store.graph_store_graph_param,
            graph_name_uri=named_graph))
        return True if response.status_code in [200, 202, 204] else False

    def get(self, named_graph, as_graph=False):
        """ Retrieve all triples from the named graph.

        :param named_graph: the uri to the named graph
        :return: Graph
        """
        headers = {'Content-Type': 'text/nt'}
        response = requests.get(
            "{graph_store_url}?{graph_param}={graph_name_uri}".format(
                graph_store_url=self.graph_store,
                graph_param=self.rdf_store.graph_store_graph_param,
                graph_name_uri=named_graph),
            headers=headers)
        if response.status_code == 404:
            raise UnknownGraph("No such graph: <{}>".format(named_graph))
        if as_graph:
            graph = Graph(identifier=named_graph)
            graph.namespace_manager = namespace_manager
            graph.parse(data=response.content, format='nt')
            return graph
        return response

    def head(self, named_graph):
        """Testing for validity of derefencable named graphs."""
        headers = {'Content-Type': 'text/nt'}
        response = requests.head(
            "{graph_store_url}?{graph_param}={graph_name_uri}".format(
                graph_store_url=self.graph_store,
                graph_param=self.rdf_store.graph_store_graph_param,
                graph_name_uri=named_graph),
            headers=headers
        )
        return True if response.status_code == 200 else False

    def post(self, named_graph, data):
        """Update the content of the named graph with information from data.
        """
        headers = {'Content-Type': 'application/n-triples; charset=utf-8'}
        rdf_string = self._get_data_as_rdf_string(data)
        r = requests.post(
            "{graph_store_url}?{graph_param}={graph_name_uri}".format(
                graph_store_url=self.graph_store,
                graph_param=self.rdf_store.graph_store_graph_param,
                graph_name_uri=named_graph),
              data=rdf_string,
              headers=headers)
        if r.status_code == 404:
            # create the graph because it does not exist
            r = requests.put(
                "{graph_store_url}?{graph_param}={graph_name_uri}".format(
                    graph_store_url=self.graph_store,
                    graph_param=self.rdf_store.graph_store_graph_param,
                    graph_name_uri=named_graph),
                 data=rdf_string,
                 headers=headers)
        if r.status_code not in [200, 201, 204]:
            logger.error("unable to store document {} in graph {} because of:\n {}".format(
                    rdf_string,
                    named_graph,
                    r.status_code
            )
            )
            return False
        logger.info("Stored RDF in {}".format(named_graph))
        return True

    def put(self, named_graph, data):
        """PUT request to replace or create the graph with information form data"""
        headers = {'Content-Type': 'text/nt'}
        rdf_string = self._get_data_as_rdf_string(data)
        r = requests.put(
            "{graph_store_url}?{graph_param}={graph_name_uri}".format(
                graph_store_url=self.graph_store,
                graph_param=self.rdf_store.graph_store_graph_param,
                graph_name_uri=named_graph),
             data=rdf_string,
             headers=headers)
        if r.status_code not in [200, 201, 204]:
            logger.error("unable to store document {} in graph {} because of bla:\n {}".format(
                    rdf_string,
                    named_graph,
                    r.status_code)
            )
            return False
        logger.info("Stored RDF in {}".format(named_graph))
        return True

    def put_file(self, file_path):
        """PUT request to replace or create the graph with information form data"""
        files = {'file': (os.path.basename(file_path), open(file_path, 'rb'), "application/n-quads")}
        r = requests.post(
            "{graph_store_url}".format(graph_store_url=self.graph_store),
            files=files,
        )
        if r.status_code not in [200, 201, 204]:
            logger.error("unable to store file {} because of bla:\n {}\n{}".format(
                file_path,
                r.status_code,
                r.raise_for_status())
            )
            return False
        logger.info("Stored RDF from {} in triple-store".format(file_path))
        return True

# test if the right database are defined
_rdfstore_test = RDFStore(db="test")
_rdfstore_acceptance = RDFStore(acceptance_mode=True)
_rdfstore_production = RDFStore()


# convenience methods to the Default RDFStore
def get_namespace_manager():
    """get the default namespace manager."""
    return namespace_manager


def get_rdfstore(acceptance_mode=False, test_mode=False):
    """get the rdfstore in the right mode."""
    store = _rdfstore_production
    if test_mode:
        store = _rdfstore_test
    elif acceptance_mode:
        store = _rdfstore_acceptance
    return store


def get_sparql_base_url(acceptance_mode=False):
    return get_rdfstore(acceptance_mode).base_url


def get_graph_store_url(acceptance_mode=False):
    return get_rdfstore(acceptance_mode).get_graph_store_url


def get_sparql_query_url(acceptance_mode=False):
    return get_rdfstore(acceptance_mode).get_sparql_query_url


def get_sparql_update_url(acceptance_mode=False):
    return get_rdfstore(acceptance_mode).get_sparql_update_url


def describe(uri, named_graph=None, acceptance_mode=False):
    return get_rdfstore(acceptance_mode=acceptance_mode).describe(uri, named_graph=named_graph)
