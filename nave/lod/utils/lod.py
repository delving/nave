# -*- coding: utf-8 -*- 
"""This module does


"""
from collections import Counter
import logging
from urllib.error import HTTPError
from urllib.parse import quote, urlparse

from django.conf import settings
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF

from lod.utils.resolver import RDFRecord

log = logging.getLogger(__name__)


