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

from django.conf import settings
from elasticutils import FACET_TYPES
from elasticutils import get_es

FACET_TYPES.append('geohash')

logger = logging.getLogger(__name__)

# Verbose name configuration for this app
default_app_config = 'search.apps.SearchConfig'


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

ES_TIMEOUT = get_settings('ES_TIMEOUT', 5)

ORG_ID = get_settings("ORG_ID", settings.SITE_NAME.lower())

# check if all the indexes are created and if not create with the right mappings
es = get_es(ES_URLS)


def get_es():
    return es


mappings = {
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
                },
                "dynamic_templates": [
                    {"dates": {
                        "match": "*_at",
                        "mapping": {
                            "type": "date",
                        }
                    }},
                    {
                        "nested_system": {
                            "match": "system",
                            "mapping": {
                                "type": "nested"
                            }
                        }
                    },
                    {"system": {
                        "path_match": "system.*",
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
                    {
                        "nested_legacy": {
                            "match": "legacy",
                            "mapping": {
                                "type": "nested"
                            }
                        }
                    },
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
                    # {
                    #     "nested_rdf": {
                    #         "match": "rdf",
                    #         "mapping": {
                    #             "type": "nested"
                    #         }
                    #     }
                    # },
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
                            "type": "string",
                            "fields": {
                                "raw": {
                                    "type": "string",
                                    "index": "not_analyzed"
                                }
                            }
                        }
                    }},
                    {"raw": {
                        "match": "raw",
                        "mapping": {
                            "type": "string",
                            "index": "not_analyzed"
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
                                    "ignore_above": 256
                                }
                            }
                        }
                    }},
                ],
            }
    }
}


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
    if es.indices.exists(index_name) and force_create:
        es.indices.delete(index=index_name)
    if not es.indices.exists(index_name):
        es.indices.create(index=index_name, body=local_mapping)
        created = True
    #else:
    #    es.indices.put_mapping(index=index_name, body=local_mapping, doc_type="void_edmrecord")
    index_aliases = es.indices.get_alias(index_name)
    logger.info("Index {} is now available with the following aliases: {}".format(index_name, index_aliases))
    return created


for index, name in list(ES_INDEXES.items()):
    create_index(
        index_name=name,
        aliases=name.replace('_v1', '')
    )
