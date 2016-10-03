# -*- coding: utf-8 -*-
"""Facets Module

This module contains all the functionality that deals with Facets.

Facets are ways to aggregrate and filter information based on their Type-Token
frequency. Usually, the top-50 most frequent unique terms from a metadata field
are returned sorted decendingly.
"""


class FacetConfig():
    """The configuration options for a Facet entry.


    """
    def __init__(self, es_field):
        """Create an FacetConfig instance.

        Args:
            es_field (str): name of target field for populating facets.
        """
        self._es_field = es_field

    @property
    def es_field(self):
        """Return the facet field used for creating the facet query.

        ElasticSearch/Lucene requires a non-analysed string for facetting.
        In our model this field is in a copy-field called 'raw'. It is accessed
        via '.' notation in the query language. Therefor, we append '.raw' to
        the facet-field

        In this function, we
        Returns:

        """
        if not self._es_field.endswith('.raw'):
            return "{}.raw".format(self._es_field)
        return self._es_field
