# -*- coding: utf-8 -*-
"""The field order on a detail page rests on one property of rdflib.

RDFResource.get_items used to natsort plain literals by value, which put
"breedte" ahead of "hoogte" no matter how a museum entered the dimensions
(#3548/#952). That sort is gone, so the page now shows values in the order the
record states them -- but only because iterating a parsed graph yields them in
document order.

That is not true of every rdflib. Measured on Python 3.9:

    rdflib 6.3.2   document order, stable across runs
    rdflib 4.2.2   a different order on every run, since the store is set-based

So this is a dependency floor, not a detail: on rdflib 4 the change would
replace a wrong-but-stable order with a random one. requirements pins 6.3.2;
this test fails loudly if that ever slips back.
"""
import unittest

import rdflib
from rdflib import Graph, URIRef

RECORD = b"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dcterms="http://purl.org/dc/terms/">
  <rdf:Description rdf:about="http://example.org/record/1">
    <dcterms:extent>breedte lijst: 66.5 cm</dcterms:extent>
    <dcterms:extent>hoogte lijst: 83 cm</dcterms:extent>
    <dcterms:extent>hoogte beeld: 59.5 cm</dcterms:extent>
    <dcterms:extent>breedte beeld: 43.7 cm</dcterms:extent>
  </rdf:Description>
</rdf:RDF>"""

# The order the source states, taken from Steendrukmuseum record 000.001.
EXPECTED = [
    "breedte lijst: 66.5 cm",
    "hoogte lijst: 83 cm",
    "hoogte beeld: 59.5 cm",
    "breedte beeld: 43.7 cm",
]

SUBJECT = URIRef("http://example.org/record/1")


class GraphOrderTestCase(unittest.TestCase):
    def test_rdflib_is_recent_enough_to_keep_order(self):
        major = int(rdflib.__version__.split(".")[0])
        self.assertGreaterEqual(
            major, 6,
            "rdflib %s iterates a set-based store, so removing the sort in "
            "get_items would randomise field order" % rdflib.__version__,
        )

    def test_parsed_graph_yields_document_order(self):
        # Repeated, because a set-based store does not fail on every run.
        for attempt in range(5):
            graph = Graph()
            graph.parse(data=RECORD, format="application/rdf+xml")

            values = [
                str(obj)
                for _, obj in graph.predicate_objects(subject=SUBJECT)
            ]

            self.assertEqual(
                values, EXPECTED,
                "attempt %d returned a different order" % attempt,
            )


if __name__ == "__main__":
    unittest.main()
