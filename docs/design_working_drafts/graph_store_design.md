# Graphstore Design Documentation

## API

* PUT: clears the graph triples and adds the new one
* POST: only adds to the graph
* DELETE: removes the graph

The following API parameters are supported:

* uri (str): the RDF subject that needs to be stored or retrieved. For put, put and delete this must always be the graphname
* context (bool; default false): If the context and three level links should be resolved 
* isGraph (bool; default true): If the uri that is given should be treated as a subject or graphname
* index (bool; default true): If the RDF stored should be synced with the index (PUT, POST, DELETE)
* sparql (bool; default true): If the RDF stored should be synced with the triple store for sparql queries
* hubId (str: optional): The hubId of the graph stored
* spec (str: optional): The dataset spec under which the RDF data should be stored. If absent the RDF is stored in a general RDF cache dir

In Django this should be implemented as a function view to easily switch between the various methods. 
All the heavy lifting should be delegated to the FsGraphStore class.


## FsGraphStore

The storage follows the same principles as the WebResource storage:

    /{root}/webresource/{org_id}/{spec}/

WHen the 'spec' dir is deleted, all traces of the dataset should be removed from disk. Later a clean-up system can be implemented that cleans up a missing 'spec' from the index and sparql-endpoint

The generic RDF cache is stored:

    
    /{root}/webresource/{org_id}/rdf/cache


The graphname has a switch based on the RDF_BASE_URL setting. if same domain it is dataset based otherwise it goes into the RDF cache dir.

For external enrichment datasources such as for example SKOS vocabularies all information is stored in:

    /{root}/webresource/{org_id}/rdf/vocabularies/{vocab_spec_name}

### Support for routed entry points

Via the settings file a number of routing entry points can be defined as a list. The main function of these routing points is that you can use a single graphstore with a unified RDF_BASE_URL that can be moved from server to server but still use different domains for serving out the LOD data. 

Note: that this resolving only goes one way. So the RDF returned only contains RDF as it is stored.

### Hash based resolving of uri's and graph-names

The full uri is converted into a sha128 string which is used for creating the path (3 layers deep) and the file name with a .nt extension. Additional information - such as webresources or mappings links - is stored as additional n-triples files in the same directory.

Future extensions could be to separate the graph out into its subject constituents but this is out of scope for the first iteration of the FsGraphStore implemetation.

The request for a graphname goes through the following steps:

    * receive uri
    * translate uri into hash
    * translate hash into full path
    * retrieve file
    * render directly or convert using RDFlib.
    
When the context is required to retrieve 3 level deep of linked records, they are retrieved via the same steps and then integrated into the triples, before giving it back.

Note that it could be possible to provide different templates for which data should be resolved and which data should be included. Ideally this could be done via specific RDF class that are available at runtime.


The expectation is that both the storage and retrieval of the RDF data stored this way will be very fast. Also the reduced overhead of having to craft custom SPARQL queries and executing them on a SPARQL endpoint will speed up matter significantly. 

For more complex queries and relationships the RDF data stored in the search engine can be used. 

## Thesaurus mapping 

The theraus mappings are stored via the API and are also dataset dependent. 

At the root of the 'spec' folder the dataset graph meta-information is stored in JSON format for fast retrieval. In this document you will find relevant information such as fields that can be enriched, access rights, harvesting information etc. It is basically the same information that is stored in triples in the Triple Store by Narthex now.

## RDF indexing with Elastic Search 
