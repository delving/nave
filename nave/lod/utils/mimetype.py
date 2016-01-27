# -*- coding: utf-8 -*-
"""
This module provides support for converting mime-types and extensions of RDF serializations that are
supported by the LoD app.

Serializations formats that are not in EXTENSION_TO_MIME_TYPE cannot be used during the 303 content negotiation and
data rendering.
"""
from .mimeparse import best_match as lib_best_match

# SPARQL results
JSON_MIME = "application/sparql-results+json"
XML_MIME = "application/sparql-results+xml"

# support RDF mime-types
HTML_MIME = "text/html"
N3_MIME = "text/n3"
TURTLE_MIME = "text/turtle"
RDFXML_MIME = "application/rdf+xml"
NTRIPLES_MIME = "application/n-triples"
JSONLD_MIME = "application/json"

EXTENSION_TO_MIME_TYPE = {"rdf": RDFXML_MIME, "n3": N3_MIME, "nt": NTRIPLES_MIME, "turtle": TURTLE_MIME,
                          "ttl": TURTLE_MIME, "json-ld": JSONLD_MIME, "json": JSONLD_MIME}
MIME_TYPE_TO_EXTENSION = dict(list(map(
        reversed,
        [(ext, mime) for ext, mime in list(EXTENSION_TO_MIME_TYPE.items()) if ext not in ['ttl', 'json']]
)))


def mime_to_extension(mime_type):
    """
    Convert mime-type from accept-headings to file extension.
    """
    if mime_type in MIME_TYPE_TO_EXTENSION:
        return MIME_TYPE_TO_EXTENSION[mime_type]
    return "rdf"


def extension_to_mime(extension):
    """Convert file extension to mime-type.

    Some have to be rewritten because the MIME type does not correspond to the file extension.
    """
    if extension == 'ttl':
        extension = 'turtle'
    if extension == 'json':
        extension = 'json-ld'
    if extension in EXTENSION_TO_MIME_TYPE:
        return extension, EXTENSION_TO_MIME_TYPE[extension]
    return "xml", RDFXML_MIME


def result_extension_to_mime(extension):
    """Convert result extension to MIME type.

     Some have to be rewritten rewritten because the MIME type does not correspond to the file extension.
    """
    if extension == 'xml':
        return XML_MIME
    if extension == 'json':
        return JSON_MIME
    if extension == 'html':
        return HTML_MIME
    return EXTENSION_TO_MIME_TYPE[extension]


def best_match(candidate, header):
    if header and 'text/html' in header:
        return ''
    if header:
        return lib_best_match(candidate, header)
    return None
