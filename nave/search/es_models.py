# coding=utf-8
"""This module contains the models for interacting ElasticSearch 2+.

The goal of these models is to index any RDF data and interact with it in a predictable way.
"""

from datetime import datetime

from django.conf import settings
from elasticsearch_dsl import DocType, String, Date, Boolean, Nested, analyzer

html_strip = analyzer('html_strip',
                      tokenizer="standard",
                      filter=["standard", "lowercase", "stop", "snowball"],
                      char_filter=["html_strip"]
                      )


class SKOSRecord(DocType):
    pass


class RDFIndexRecord(DocType):
    spec = String(index='not_analyzed')
    modified_at = Date()
    hub_id = String(index='not_analyzed')
    hasGeoHash = Boolean()
    hasDigitalObject = Boolean()
    hasDeepZoom = Boolean()
    hasEnrichmentLink = Boolean()
    published = Boolean()
    # dataSourceType => enum: Primary, Aggregated, Cached, Thesaurus/SKOS
    # category = String(
    #     analyzer=html_strip,
    #     fields={'raw': String(index='not_analyzed')}
    # )

    # rdf
    # proxy_resources
    # web_resources

    # comments = Nested(
    #     properties={
    #         'author': String(fields={'raw': String(index='not_analyzed')}),
    #         'content': String(analyzer='snowball'),
    #         'created_at': Date()
    #     }
    # )

    class Meta:
        index = settings.SITE_NAME

    # def add_comment(self, author, content):
    #     self.comments.append(
    #         {'author': author, 'content': content})

    def save(self, ** kwargs):
        self.modified_at = datetime.now()
        return super().save(** kwargs)
