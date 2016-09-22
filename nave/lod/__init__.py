# -*- coding: utf-8 -*-
"""
The LoD app is initialised here.

We make a number of convenience functions and variables available at the root of the app.

In addition we check if the right settings are configured in the settings.py.
"""
import logging
import os

import requests
from django.conf import settings
from rdflib import Graph
from rdflib.namespace import NamespaceManager, Namespace

from lod.utils.mimetype import EXTENSION_TO_MIME_TYPE

logger = logging.getLogger(__name__)

# Verbose name configuration for this app
default_app_config = 'lod.apps.LoDConfig'

# Default settings

# Use the EDM resource bindings and template to render EDM LoD HTML pages
USE_EDM_BINDINGS = False

# The database name of the RDF store
RDF_STORE_DB = None

try:
    RDF_STORE_DB = settings.RDF_STORE_DB
except AttributeError as e:
    raise AttributeError("""Variable RDF_STORE_DB must be defined in the settings.py """)

try:
    # The hostname were the triple store is running
    RDF_STORE_HOST = settings.RDF_STORE_HOST

    # The port where the triple store is reachable at
    RDF_STORE_PORT = settings.RDF_STORE_PORT

    # the base url of the RDF resources that will be served by this django LoD app
    RDF_BASE_URL = settings.RDF_BASE_URL

    # the supported namespaces that we use in our graphs. This is used for the RDFlib namespacemanager
    RDF_SUPPORTED_NAMESPACES = settings.RDF_SUPPORTED_NAMESPACES

    RDF_ROUTED_ENTRY_POINTS = settings.RDF_ROUTED_ENTRY_POINTS

    RDF_STORE_TYPE = settings.RDF_STORE_TYPE

except AttributeError as e:

    raise AttributeError("""
    The following settings (with example values) need to be defined in the Django *settings.py*

    # The hostname were the triple store is running
    RDF_STORE_HOST = "http://localhost"

    # The port where the triple store is reachable at
    RDF_STORE_PORT = 3030

    # the base url of the RDF resources that will be served by this django LoD app (no scheme prefix!!)
    RDF_BASE_URL = 'prod.lod.com'

    RDF_ROUTED_ENTRY_POINTS = ['localhost:8000', 'acc.lod.com']
                                                    ¡
    # the supported namespaces that we use in our graphs. This is used for the RDFlib namespacemanager
    RDF_SUPPORTED_NAMESPACES = {{
        'http://purl.org/abm/sen': 'abm',
        'http://www.europeana.eu/schemas/ese/': 'europeana',
        'http://purl.org/dc/elements/1.1/': 'dc',
        'http://schemas.delving.eu/': 'delving',
        'http://purl.org/dc/terms/': 'dcterms',
    }}

    Optional settings:

    # Set the type of RDF_STORE. Currently, "BlazeGraph" and "Fuseki" are supported.
    RDF_STORE_TYPE = "Fuseki"

    # when set to true EDM resources are bound differently and get their own presentation layer.
    USE_EDM_BINDINGS = True

    Actual Exception:
    {}
    """.format(e))

# Optional Settings defined from Django settings.py

try:
    USE_EDM_BINDINGS = settings.USE_EDM_BINDINGS
except AttributeError as e:
    USE_EDM_BINDINGS = True

# Other convenience variables.

RDF_SUPPORTED_MIME_TYPES = list(EXTENSION_TO_MIME_TYPE.values())

RDF_SUPPORTED_EXTENSIONS = list(EXTENSION_TO_MIME_TYPE.keys())

namespace_manager = NamespaceManager(Graph())

for uri, ns in list(settings.RDF_SUPPORTED_NAMESPACES.items()):
    namespace_manager.bind(ns, Namespace(uri), override=False)


# test if all databases are defined
# TOdo add  "{}_acceptance".format(RDF_STORE_DB),
# TODO review the URL composition below:
for db in ["{}".format(RDF_STORE_DB), "test"]:
    try:
        response = requests.get(
            "http://{}:{}/{}/sparql?query=ask+where+{{%3Fs+%3Fp+%3Fo}}&output=json&stylesheet=".format(
                os.environ.get('FUSEKI_PORT_3030_TCP_ADDR', 'localhost'),
                os.environ.get('FUSEKI_PORT_3030_TCP_PORT', '3030'),
                db
            )
        )
        if response.status_code != 200:
            raise ConnectionError()
    except Exception as err:
        logger.error(
            """
            Missing db: {db}

            Please make sure the following database are configured in the RDF store:

            * {store}
            * {store}_acceptance
            * test

            For Fuseki an example configuration would look as follows:

            # Licensed under the terms of http://www.apache.org/licenses/LICENSE-2.0

            ## Basic Fuseki configuation file.
            ##
            ## See also config-tdb.ttl for TDB specific examples.
            ## See also config-examples.ttl for commented examples.

            @prefix :        <#> .
            @prefix fuseki:  <http://jena.apache.org/fuseki#> .
            @prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

            @prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
            @prefix tdb:     <http://jena.hpl.hp.com/2008/tdb#> .
            @prefix ja:      <http://jena.hpl.hp.com/2005/11/Assembler#> .

            [] rdf:type fuseki:Server ;
            # Timeout - server-wide default: milliseconds.
            # Format 1: "1000" -- 1 second timeout
            # Format 2: "10000,60000" -- 10s timeout to first result, then 60s timeout for the rest of query.
            # See java doc for ARQ.queryTimeout
            # ja:context [ ja:cxtName "arq:queryTimeout" ;  ja:cxtValue "10000" ] ;

            # ja:loadClass "your.code.Class" ;

            fuseki:services (
            <#{db}s_service>
            ) .

            ## ---------------------------------------------------------------
            <#{db}s_service>  rdf:type fuseki:Service ;
            fuseki:name              	       "{db}s" ;       # http://host:port/tdb
            fuseki:serviceQuery                "sparql" ;
            fuseki:serviceQuery                "query" ;
            fuseki:serviceUpdate               "update" ;
            fuseki:serviceUpload               "upload" ;
            fuseki:serviceReadWriteGraphStore  "data" ;
            fuseki:serviceReadGraphStore       "get" ;
            fuseki:dataset           		   <{db}s> ;
            .

            <{db}s> rdf:type      tdb:DatasetTDB ;
                tdb:location                        "/opt/fuseki/run/databases/{db}s";
                # Query timeout on this dataset (1s, 1000 milliseconds)
                ja:context [ ja:cxtName "arq:queryTimeout" ;  ja:cxtValue "4000,20000" ] ;
                # Make the default graph be the union of all named graphs.
                tdb:unionDefaultGraph               true;
                .


            # end of configuration file

            This file needs to be save to $FUSEKI_HOME/run/configuration and you then need to restart.

            For a full configuration that is used during standard provisioning see deploy/fuseki_production.ttl

            """.format(db=db, store=RDF_STORE_DB)
        )
