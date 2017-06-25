# -*- coding: utf-8 -*-
"""
Here the search app is initialised and the settings verified

The following settings are Optional for this app

    * ES_URLS: the elasticsearch urls
    * ES_DISABLED: if elasticsearch is disabled. Useful for testing
    * ES_INDEXES: a dictionary of elasticsearch indices. At least default, acceptance, and test need to be defined.
    * ES_TIMEOUT: the search timeout
    * ORG_ID: for legacy purposes we need the name of the organisation. By default it is the sitename in lowercase.

"""
import logging
from collections import namedtuple
import sys

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import ConnectionError, TransportError

logger = logging.getLogger(__name__)

# Verbose name configuration for this app
default_app_config = 'nave.search.apps.SearchConfig'


LayoutItem = namedtuple("LayoutItem", ["name", "i18n"])


def get_settings(setting_name, default_value):
    """Utility function for getting values from the settings.py.
    :param setting_name:
    :param default_value:
    """
    return getattr(settings, setting_name, default_value)


# default settings

ES_URLS = get_settings('ES_URLS', ['localhost:9200'])

ES_DISABLED = get_settings('ES_DISABLED', False)  # useful for debugging

ES_INDEXES = get_settings('ES_INDEXES', {
    'default': '{}_v1'.format(settings.SITE_NAME),
    'acceptance': '{}_acceptance_v1'.format(settings.SITE_NAME),
})

ES_TIMEOUT = get_settings('ES_TIMEOUT', 10)

ORG_ID = get_settings("ORG_ID", settings.SITE_NAME.lower())

# check if all the indexes are created and if not create with the right mappings
try:
    connections.create_connection(
        hosts=ES_URLS,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        maxsize=25,  # default value 10
        timeout=ES_TIMEOUT,
    )
except (ConnectionError, TransportError) as ce:
    msg = "Unable to connect to Elasticsearch hosts: {}".format(ES_URLS)
    logger.error(msg)
    print(msg)
    sys.exit(1)


def get_es_client():
    return Elasticsearch(
        hosts=ES_URLS,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        maxsize=25,  # default value 10
        timeout=ES_TIMEOUT,
    )

es_client = get_es_client()

# test connection
try:
    es_client.ping()
except (ConnectionError, TransportError) as ce:
    logger.error(
        "Unable to connect to Elasticsearch hosts: {}".format(ES_URLS)
    )
    sys.exit(1)


mappings = {
    "settings": {
        "analysis": {
            "filter": {
                "dutch_stop": {
                    "type":       "stop",
                    "stopwords":  "_dutch_"
                },
                # "dutch_keywords": {
                    # "type":       "keyword_marker",
                    # "keywords":   []
                # },
                "dutch_stemmer": {
                    "type":       "stemmer",
                    "language":   "dutch"
                },
                "dutch_override": {
                    "type":       "stemmer_override",
                    "rules": [
                        "fiets=>fiets",
                        "bromfiets=>bromfiets",
                        "ei=>eier",
                        "kind=>kinder"
                    ]
                }
            },
            "analyzer": {
                "dutch": {
                    "tokenizer":  "standard",
                    "filter": [
                        "lowercase",
                        "dutch_stop",
                        # "dutch_keywords",
                        "dutch_override",
                        "dutch_stemmer"
                    ]
                }
            }
        }
    },
    "mappings": {
        "_default_":
            {
                "_all": {
                    "enabled": True
                },
                "date_detection": False,
                'properties': {
                    'id': {'type': 'integer'},
                    'absolute_url': {'type': 'string'},
                    "point": {
                        "type": "geo_point"
                    },
                    "delving_geohash": {
                        "type": "geo_point"
                    },
                    "system": {
                        'properties': {'about_uri': {'fields': {'raw': {
                            'index': 'not_analyzed',
                            'type': 'string'}},
                            'type': 'string'},
                            'caption': {'fields': {'raw': {
                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                            'created_at': {'format': 'dateOptionalTime', 'type': 'date'},
                            'graph_name': {'fields': {'raw': {
                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                            'modified_at': {'format': 'dateOptionalTime', 'type': 'date'},
                            'preview': {'fields': {'raw': {
                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                            'slug': {'fields': {'raw': {
                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                            'source_graph': {
                                'index': 'no',
                                'type': 'string',
                                'doc_values': False
                            },
                            "geohash": {
                                "type": "geo_point"
                            },
                            'source_uri': {'fields': {'raw': {

                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                            'spec': {'fields': {'raw': {
                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                            'thumbnail': {'fields': {'raw': {
                                'index': 'not_analyzed',
                                'type': 'string'}},
                                'type': 'string'},
                        }
                    }
                },
                "dynamic_templates": [
                    {"dates": {
                        "match": "*_at",
                        "mapping": {
                            "type": "date",
                        }
                    }},
                    {"legacy": {
                        "path_match": "legacy.*",
                        # "match_mapping_type": "string",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed",
                            "fields": {
                                "raw": {
                                    "type": "string",
                                    "index": "not_analyzed"
                                },
                                "value": {
                                    "type": "string",
                                }
                            }
                        }
                    }},
                    {"rdf": {
                        "path_match": "rdf.*",
                        # "match_mapping_type": "string",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed",
                            "fields": {
                                "raw": {
                                    "type": "string",
                                    "index": "not_analyzed"
                                },
                                "value": {
                                    "type": "string",
                                }
                            }
                        }
                    }},
                    {"uri": {
                        "match": "id",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }},
                    {"point": {
                        "match": "point",
                        "mapping": {
                            "type": "geo_point",
                        }
                    }},
                    {"geo_hash": {
                        "match": "delving_geohash",
                        "mapping": {
                            "type": "geo_point",
                        }
                    }},
                    {"value": {
                        "match": "value",
                        "mapping": {
                            "type": "string"
                        }
                    }},
                    {"raw": {
                        "match": "raw",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed",
                            "ignore_above": 1024
                        }
                    }},
                    {"id": {
                        "match": "id",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }},
                    {"graphs": {
                        "match": "*_graph",
                        "mapping": {
                            "type": "string",
                            "index": "no"
                        }
                    }},
                    {"inline": {
                        "match": "inline",
                        "mapping": {
                            "type": "object",
                            "include_in_parent": True,
                        }
                    }},
                    {"strings": {
                        "match_mapping_type": "string",
                        "mapping": {
                            "type": "string",
                            "fields": {
                                "raw": {
                                    "type": "string",
                                    "index": "not_analyzed",
                                    "ignore_above": 1024
                                }
                            }
                        }
                    }}
                ]
            }
    }}


def create_index(index_name, aliases=None, mapping=None, force_create=False):
    created = False
    local_mapping = mappings.copy()
    if aliases:
        filters = {}
        if isinstance(aliases, dict):
            for key, value in aliases.items():
                if not value:
                    value = {}
                filters[key] = value
        elif isinstance(aliases, (str, list)):
            if isinstance(aliases, str):
                aliases = [aliases]
                for alias in aliases:
                    filters[alias] = {}
        local_mapping['aliases'] = filters
    if es_client.indices.exists(index_name) and force_create:
        es_client.indices.delete(index=index_name)
    if not es_client.indices.exists(index_name):
        es_client.indices.create(index=index_name, body=local_mapping)
        created = True
    #else:
    #    es_client.indices.put_mapping(index=index_name, body=local_mapping, doc_type="void_edmrecord")
    index_aliases = es_client.indices.get_alias(index_name)
    logger.info("Index {} is now available with the following aliases: {}".format(index_name, index_aliases))
    return created


for index, name in list(ES_INDEXES.items()):
    create_index(
        index_name=name,
        aliases=name.replace('_v1', '')
    )
