Linked Open Data app
====================

This app is designed to provide all basic Linked Open Data functionality on top of any *RDF store* (i.e. triple-store)
that supports `SPARQL 1.1 <http://www.w3.org/TR/rdf-sparql-query/>` and
`Graph Store protocol <http://www.w3.org/TR/sparql11-http-rdf-update/>_`.

It provides the following functionality:

* 303 content negotiation
   * /resource as entry point
   * /page for the HTML view
   * /data for an RDF serialization
* /sparql proxy for SPARQL query. (The others are not available from the web)
* /snorql SPARQL query exploration app
    * access to stored example queries
    * saving in different output formats
* /relfinder visualisation of Graph relations
* sparqlutils for building sparql queries
* Graph normalisation to can be used for
    * indexing related content via links
    * presenting related content in line in the view layer


Settings
--------

This app requires the following settings to be defined in the Django *settings.py*.

** RDF_STORE_HOST **: a fully qualified url where the RDF
** RDF_STORE_PORT **: the port where the RDF-store is accessible
** RDF_BASE_URL **: the base url for the resources that will be served by this Lod routing app.
** RDF_SUPPORTED_NAMESPACES **: a dict of namespaces that will be resolved when serializing RDF


Optional settings:

** RDF_STORE_DB **: the database name used in the RDF store
** USE_EDM_BINDINGS **: boolean to define if the EDM bindings are used in the HTML rendering of EDM resources

Currently, we fully support `Fuseki <http://jena.apache.org/documentation/serving_data/>_` but other RDF-stores
like *virtuoso*, *stardog*, etc. should work out of the box as well.


# detail page

## LOD data right fold-out

• statistics (each has link of tuples with name and link)
	◦	rdf class 
	◦	rdf property
	◦	dataset (where does the data belong)
	◦	cache resource (the source of the link, e.g. dbpedia, geonames)
	◦	skos vocabulary (which vocabularies are now linked)
	◦	record types (aggregation, primary, cached, skos )
	◦	geo
	◦	languages


•	lightbox
	◦	load and display resource (cached, vocabulary, etc. )


•	link creation
	◦	icons
        ▪	pen: edit add link
        ▪	loop: open lightbox
        ▪	arrow out of box: go to page of link
	◦	form
        ▪	field_name
        ▪	literal
        ▪	link
        ▪	save button


## Search Page

* lod data fold-out with lod facets (these are normal facets from the view as variable)

