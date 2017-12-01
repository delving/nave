# -*- coding: utf-8 -*-
"""
This module contains the convertors of EDM resource graphs (saved in a Named Graph) into
legacy flat formats. We currently support:

    * ESE
    * EDM strict
    * ABM
    * TIB
    * ICN

These conversion can be used in OAI-PMH or API search and detail outputs.
"""
import collections
import copy
import json
import logging
import re
from collections import defaultdict

from django.conf import settings
from django.utils.translation import ugettext as _
from lxml import etree as ET
from rdflib import URIRef, Literal

from nave.lod import namespace_manager
from nave.lod.utils.resolver import GraphBindings
from nave.lod.utils.rdfstore import get_rdfstore, UnknownGraph
from nave.lod.utils.resolver import RDFRecord

logger = logging.getLogger(__name__)


class BaseConverter(object):
    """
    Convert a graph into a flat legacy format

    Dict
    """
    _allowed_field = []

    def __init__(self, about_uri=None, graph=None, es_result_fields=None, bindings=None, allowed_fields=None,
                 org_id=settings.ORG_ID):
        self.org_id = org_id
        self.about_uri = about_uri
        self._es_result_fields = es_result_fields
        self._bindings = bindings
        self.allowed_fields = allowed_fields if allowed_fields else []
        self.graph = graph
        self._used_namespaces = None
        self._mapping_dict = None
        self._field_dict = defaultdict(list)

    def bindings(self):
        if not self._bindings and self.graph:
            self._bindings = GraphBindings(graph=self.graph, about_uri=self.about_uri)
        return self._bindings

    def add_allowed_field(self, field_property):
        pass

    def get_field_dict(self):
        raise NotImplementedError("implement me")

    def get_namespace(self):
        raise NotImplementedError("implement me")

    def get_namespaces(self, as_ns_declaration=False):
        if not self._used_namespaces:
            bindings = self.bindings()
            mapping_keys = self.get_mapping_dict().keys()
            prefixes = {key.split('_')[0] for key in mapping_keys}
            self._used_namespaces = [(prefix, settings.RDF_SUPPORTED_PREFIXES[prefix]) for prefix in prefixes]
        if as_ns_declaration:
            return " ".join(['xmlns:{}="{}"'.format(ns, ns_uri[0]) for ns, ns_uri in self._used_namespaces])
        return self._used_namespaces

    def get_converter_key(self):
        raise NotImplementedError("implement me")

    def shared_field_dict(self):
        mapping = {
            "dc_title": "dc_title",
            "dc_Title": "dc_Title",
            "dc_creator": "dc_creator",
            "dc_subject": "dc_subject",
            "dc_description": "dc_description",
            "dc_publisher": "dc_publisher",
            "dc_contributor": "dc_contributor",
            "dc_date": "dc_date",
            "dc_type": "dc_type",
            "dc_format": "dc_format",
            "dc_identifier": "dc_identifier",
            "dc_source": "dc_source",
            "dc_language": "dc_language",
            "dc_relation": "dc_relation",
            "dc_coverage": "dc_coverage",
            "dc_rights": "dc_rights",
            "dcterms_created": "dcterms_created",
            "dcterms_extent": "dcterms_extent",
            "dcterms_hasFormat": "dcterms_hasFormat",
            "dcterms_hasPart": "dcterms_hasPart",
            "dcterms_hasVersion": "dcterms_hasVersion",
            "dcterms_isFormatOf": "dcterms_isFormatOf",
            "dcterms_isPartOf": "dcterms_isPartOf",
            "dcterms_isReferencedBy": "dcterms_isReferencedBy",
            "dcterms_isReplacedBy": "dcterms_isReplacedBy",
            "dcterms_isRequiredBy": "dcterms_isRequiredBy",
            "dcterms_isVersionOf": "dcterms_isVersionOf",
            "dcterms_issued": "dcterms_issued",
            "dcterms_medium": "dcterms_medium",
            "dcterms_references": "dcterms_references",
            "dcterms_replaces": "dcterms_replaces",
            "dcterms_requires": "dcterms_requires",
            "dcterms_tableOfContents": "dcterms_tableOfContents",
            "dcterms_alternative": "dcterms_alternative",
            "dcterms_spatial": "dcterms_spatial",
            "dcterms_temporal": "dcterms_temporal",
            "dcterms_provenance": "dcterms_provenance",
            "dcterms_rightsHolder": "dcterms_rightsHolder",
            "europeana_isShownBy": "edm_isShownBy",
            "europeana_rights": "edm_rights",
            "europeana_isShownAt": "edm_isShownAt",
            "europeana_unstored": "edm_unstored",
            "europeana_object": "edm_object",
            "europeana_provider": "edm_provider",
            "europeana_dataProvider": "edm_dataProvider",
            "europeana_type": "edm_type",
            "europeana_uri": "edm_uri",
            "europeana_language": "edm_language",
            "europeana_country": "edm_country",
            "europeana_collectionName": "edm_collectionName",
            "europeana_collectionTitle": "edm_collectionTitle",
            "europeana_source": "edm_source",
        }
        return mapping

    @staticmethod
    def query_key_replace_dict(reverse=False):
        raise NotImplementedError("implement me")

    def delving_mapping(self):
        return {
            "delving_year": "delving_year",
            "delving_thumbnail": "nave_thumbnail",
            "delving_deepZoomUrl": "nave_deepZoomUrl",
            "delving_fullTextObjectUrl": "nave_fullTextObjectUrl",
            "delving_fullText": "nave_fullText",
            "delving_geohash": "point"
        }

    @staticmethod
    def get_translated_field(key, translate=True):
        normalised_key = re.sub("abm_|tib_|icn_|delving_", 'nave_', key)
        normalised_key = re.sub("europeana_", 'edm_', normalised_key)
        if any(
            [
                normalised_key.endswith(legacy_suffix)
                for legacy_suffix in ['_string', '_facet', '_text']
             ]):
            normalised_key = "_".join(normalised_key.split("_")[:-1])
        if translate:
            return _(normalised_key)
        return normalised_key

    def get_layout_fields(self):
        layout_fields = [collections.OrderedDict(**{"name": key, "i18n": self.get_translated_field(key)}) for key in
                         self.get_mapping_dict().keys()]
        return layout_fields

    def get_mapping_dict(self):
        if not self._mapping_dict:
            mapping = self.shared_field_dict().copy()
            mapping.update(self.get_field_dict())
            self._mapping_dict = mapping
        return self._mapping_dict

    def _get_inline_links(self):
        """Return all object links that are of type ore:Aggregation. """
        inline_links = defaultdict(list)
        if self.about_uri:
            about_uri = URIRef(self.about_uri)
            about_base = re.search("(.*?/resource/.*?/).*", self.about_uri).groups()[0]
            for pred, link in self.graph.predicate_objects():
                if link.startswith(about_base) and link != about_uri:
                    inline_links[pred].append(str(link))
        return inline_links

    def _get_inline_preview(self, link, store=None):
        """Query RDFstore for graph and convert selected fields to JSON dictionary. """
        graph = None
        try:
            if settings.RDF_USE_LOCAL_GRAPH:
                record = RDFRecord(source_uri=link)
                if record.exists():
                    graph = record.get_graph()
                else:
                    raise UnknownGraph("unable to find {}".format(link))
            else:
                if not store:
                    store = get_rdfstore()
                store = store.get_graph_store
                named_graph = "{}/graph".format(link.rstrip('/'))
                graph = store.get(named_graph=named_graph, as_graph=True)
        except UnknownGraph as ug:
            logger.warn("Unable to find Graph for: {}".format(link))
            return None
        preview_fields = settings.EDM_API_INLINE_PREVIEW
        preview_predicates = [URIRef(pred) for pred in preview_fields.keys()]
        inline_dict = {}
        for pred, obj in graph.predicate_objects():
            if pred in preview_predicates:
                inline_dict[preview_fields[str(pred)]] = str(obj)
        if 'delving_hubId' in preview_fields.values():
            hub_id, spec = self.get_hub_id()
            inline_dict['delving_hubId'] = hub_id
        return inline_dict

    def get_inline_dict(self, links=None, store=None):
        """ Extract all EDM links from the graph and return a dict with enrichments.
        """
        if not self.about_uri:
            return {}
        if not store:
            store = get_rdfstore()
        if not links:
            links = self._get_inline_links()
        inline_links = {}
        for pred, links in links.items():
            for link in links:
                preview = self._get_inline_preview(link=link, store=store)
                if preview:
                    inline_links[(pred, link)] = preview
        return inline_links

    def _update_graph_with_inlines(self, inline_dict):
        """Update the graph with inlines and remove original links."""
        graph = self.graph
        for key, preview in inline_dict.items():
            pred, obj = key
            obj = URIRef(obj)
            for subj, _, _ in graph.triples((None, pred, obj)):
                graph.remove((subj, pred, obj))
                graph.add((subj, pred, Literal("\"{}\"".format(json.dumps(preview)))))
        return graph

    def convert(self, add_delving_fields=True, store=None):
        mapping = self.get_mapping_dict()
        output_doc = defaultdict(list)
        if self.get_converter_key() in settings.CONVERTERS_WITH_INLINE_PREVIEWS:
            inline_links = self._get_inline_links()
            if inline_links:
                inline_dict = self.get_inline_dict(links=inline_links, store=store)
                self._update_graph_with_inlines(inline_dict=inline_dict)
        if add_delving_fields:
            mapping.update(self.delving_mapping())
        if self._es_result_fields:
            index_doc = self._es_result_fields
            self.about_uri = index_doc['system']['about_uri']
        elif self.bindings():
            index_doc = self.bindings().to_flat_index_doc()
        else:
            raise ValueError("Unable to convert due to missing bindings or es_fields")
        # add custom fields
        for k in index_doc.keys():
            if k.startswith('custom_'):
                mapping[k] = k
            if k.startswith('nave_'):
                if '_resource' in k or '_location' in k:
                    mapping[k.replace('nave_', 'delving_')] = k
        for key, index_doc_key in mapping.items():
            if isinstance(index_doc_key, str):
                values = index_doc.get(index_doc_key)
                if values:
                    for entry in values:
                        if isinstance(entry, dict):
                            output_doc[key].append(entry['value'])
                        else:
                            output_doc[key].append(entry)
        if add_delving_fields:
            self.add_defaults(output_doc, index_doc)
        return collections.OrderedDict(sorted(output_doc.items()))

    def get_hub_id(self):
        *rest, spec, local_id = self.about_uri.split('/')
        local_id = RDFRecord.clean_local_id(local_id)
        return "{}_{}_{}".format(self.org_id, spec, local_id), spec

    def get_non_null(self, key, input_doc, output_doc):
        value = input_doc.get(key)
        if value not in [None, 'null']:
            output_doc[key] = [value]

    def add_defaults(self, output_doc, index_doc):
        output_doc['delving_recordType'] = ["mdr"]
        hub_id, spec = self.get_hub_id()
        output_doc['delving_hubId'] = [hub_id]
        output_doc['delving_pmhId'] = [hub_id]
        output_doc['delving_spec'] = [spec]
        output_doc['europeana_uri'] = ["/".join(hub_id.split('_')[1:])]
        if 'delving_resourceUri' in output_doc:
            output_doc['europeana_object'] = output_doc['delving_resourceUri']
        output_doc["delving_hasDigitalObject"] = ['europeana_object' in output_doc]
        if 'europeana_object' in output_doc:
            if 'delving_thumbnail' in output_doc:
                output_doc['delving_thumbnail'].extend(output_doc.get('europeana_object'))
            output_doc["delving_thumbnail"] = output_doc.get('europeana_object')
        if 'delving_locationLatLong' in output_doc:
            output_doc['delving_geoHash'] = output_doc['delving_locationLatLong']
        output_doc["delving_hasGeoHash"] = ['delving_geoHash' in output_doc]
        if 'europeana_isShownAt' in output_doc:
            shown_at = output_doc.get('europeana_isShownAt')
            if isinstance(shown_at, list):
                if any(e.startswith('file:///opt') for e in shown_at):
                    del output_doc['europeana_isShownAt']
            elif isinstance(shown_at, str):
                if shown_at.startswith('file:///opt'):
                    del output_doc['europeana_isShownAt']
            else:
                output_doc["delving_landingpage"] = output_doc.get('europeana_isShownAt')
        output_doc["delving_hasLandingPage"] = ['europeana_isShownAt' in output_doc]
        output_doc["europeana_collectionName"] = [spec]
        if 'legacy' in index_doc:
            legacy = index_doc.get('legacy')
            self.get_non_null('delving_collection', legacy, output_doc)
            self.get_non_null('delving_title', legacy, output_doc)
            self.get_non_null('delving_recordType', legacy, output_doc)
            self.get_non_null('delving_creator', legacy, output_doc)
            # legacy.get('delving_description', output_doc)
            self.get_non_null('delving_owner', legacy, output_doc)
            self.get_non_null('delving_provider', legacy, output_doc)
            legacy.get('delving_orgId', output_doc)
            output_doc['delving_orgId'] = [self.org_id]


class DefaultAPIV2Converter(BaseConverter):
    @staticmethod
    def query_key_replace_dict(reverse=False):
        return {}

    def get_field_dict(self):
        return {}

    def get_namespace(self):
        return None

    def get_converter_key(self):
        return "v2"

    def convert(self, add_delving_fields=False):
        if self._es_result_fields:
            index_doc = copy.deepcopy(self._es_result_fields)
            self.about_uri = index_doc['system']['about_uri']
        elif self.bindings():
            index_doc = self.bindings().to_flat_index_doc()
        else:
            raise ValueError("Unable to convert due to missing bindings or es_fields")
        if 'rdf' in index_doc:
            del index_doc['rdf']
        output_doc = copy.deepcopy(index_doc)
        for k, value_list in index_doc.items():
            if k.startswith("narthex_"):
                del output_doc[k]
                continue
            for values in output_doc[k]:
                if 'raw' in values:
                    del values['raw']
        return collections.OrderedDict(sorted(output_doc.items()))


class TIBConverter(BaseConverter):
    @staticmethod
    def query_key_replace_dict(reverse=False):
        replace_dict = {
            'europeana_': 'edm_',
            'tib_': 'nave_'
        }
        if reverse:
            replace_dict = {val: key for key, val in replace_dict.items()}
        return replace_dict

    def get_converter_key(self):
        return "tib"

    def get_namespace(self):
        return "http://schemas.delving.eu/resource/ns/tib/"

    def get_field_dict(self):
        mapping = {
            "tib_citName": "nave_citName",
            "tib_citOldId": "nave_citOldId",
            "tib_thumbLarge": "nave_thumbLarge",
            "tib_thumbSmall": "nave_thumbSmall",
            "tib_collection": "nave_collection",
            "tib_creatorRole": "nave_creatorRole",
            "tib_productionPeriod": "nave_productionPeriod",
            "tib_productionStart": "nave_productionStart",
            "tib_productionEnd": "nave_productionEnd",
            "tib_creatorBirthYear": "nave_creatorBirthYear",
            "tib_creatorDeathYear": "nave_creatorDeathYear",
            "tib_formatted": "nave_formatted",
            "tib_year": "nave_year",
            "tib_dimension": "nave_dimension",
            "tib_objectNumber": "nave_objectNumber",
            "tib_objectSoort": "nave_objectSoort",
            "tib_material": "nave_material",
            "tib_place": "nave_place",
            "tib_technique": "nave_technique",
            "tib_color": "nave_color",
            "tib_colorHex": "nave_colorHex",
            "tib_design": "nave_design",
            "tib_exhibition": "nave_exhibition",
            "tib_subjectDepicted": "nave_subjectDepicted",
            "tib_date": "nave_date",
            "tib_collectionPart": "nave_collectionPart",
            "tib_person": "nave_person",
            "tib_region": "nave_region",
            "tib_event": "nave_event",
            "tib_theme": "nave_theme",
            "tib_pageStart": "nave_pageStart",
            "tib_pageEnd": "nave_pageEnd",
            "tib_pages": "nave_pages",
            "tib_vindplaats": "nave_vindplaats",
            "tib_location": "nave_location",
            "tib_imageCopyright": "nave_imageCopyright",
            "tib_imageCreator": "nave_imageCreator",
        }

        return mapping


class ESEConverter(BaseConverter):
    @staticmethod
    def query_key_replace_dict(reverse=False):
        replace_dict = {
            'europeana_': 'edm_'
        }
        if reverse:
            replace_dict = {val: key for key, val in replace_dict.items()}
        return replace_dict

    def get_converter_key(self):
        return "ese"

    def get_namespace(self):
        return "http://www.europeana.eu/schemas/ese/"

    def get_field_dict(self):
        # only return the base mappings for ESE
        return {}


class EDMStrictConverter(BaseConverter):
    @staticmethod
    def query_key_replace_dict(reverse=False):
        replace_dict = {
            'europeana_': 'edm_'
        }
        if reverse:
            replace_dict = {val: key for key, val in replace_dict.items()}
        return replace_dict

    def get_converter_key(self):
        return "edm-strict"

    def get_namespace(self):
        return "http://www.europeana.eu/schemas/edm/"

    def get_field_dict(self):
        return {}

    supported_rdf_types = [
        "http://www.openarchives.org/ore/terms/Aggregation",
        "http://www.europeana.eu/schemas/edm/ProvidedCHO",
        "http://www.europeana.eu/schemas/edm/Place",
        "http://www.europeana.eu/schemas/edm/Agent",
        "http://www.europeana.eu/schemas/edm/TimeSpan",
        "http://www.europeana.eu/schemas/edm/Organisation",
        "http://www.europeana.eu/schemas/edm/WebResource",
        "http://www.w3.org/2004/02/skos/core#Concept",
    ]

    def _value_string_formatted(self):
        rdf_types = ["(<{}>)".format(rdf_type) for rdf_type in self.supported_rdf_types]
        return "\n".join(rdf_types)

    @staticmethod
    def uri_to_namespaced_tag(uri):
        if '#' in uri:
            elements = uri.split('#')
            split_key = '#'
        else:
            elements = uri.split('/')
            split_key = '/'
        label = elements[-1]
        prefix = "/".join(elements[:-1])
        return "{{{}{}}}{}".format(prefix, split_key, label)

    def make_rdf_xml_serialization_europeana_proof(self, rdf_xml_string):
        record = ET.fromstring(rdf_xml_string)
        for description in record.getchildren():
            rdf_types = description.findall("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}type")
            rdf_type_values = [rdf_type.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource') for rdf_type
                               in rdf_types]
            if any([rdf_type in self.supported_rdf_types for rdf_type in rdf_type_values]):
                type_tag = None
                for rdf_type in rdf_types:
                    description.remove(rdf_type)
                for val in rdf_type_values:
                    if val in self.supported_rdf_types:
                        type_tag = val
                for aggr in description.findall('{http://www.openarchives.org/ore/terms/}aggregates'):
                    description.remove(aggr)
                if type_tag:
                    rdf_about = description.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about')
                    if rdf_about:
                        new_description_tag = ET.SubElement(record, self.uri_to_namespaced_tag(type_tag))
                        new_description_tag.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about'] = rdf_about
                        for child in description.getchildren():
                            new_description_tag.append(child)
            record.remove(description)
        return ET.tostring(record, encoding="utf-8", pretty_print=True)

    def convert(self, output_format="json", add_delving_fields=True):
        graph = self.bindings()._graph
        graph.namespace_manager = namespace_manager
        if output_format is 'xml':
            output = graph.serialize(format="xml")
            output = self.make_rdf_xml_serialization_europeana_proof(output)
            return output
        else:
            context_dict = {"{}".format(prefix): namespace for prefix, namespace in
                            graph.namespace_manager.namespaces()}
            output = graph.serialize(format='json-ld', context=context_dict).decode('utf-8')
        return json.loads(output)


class EDMConverter(BaseConverter):

    @staticmethod
    def query_key_replace_dict(reverse=False):
        replace_dict = {
            'europeana_': 'edm_'
        }
        if reverse:
            replace_dict = {val: key for key, val in replace_dict.items()}
        return replace_dict

    def get_converter_key(self):
        return "edm"

    def get_namespace(self):
        return "http://www.europeana.eu/schemas/edm/"

    def get_field_dict(self):
        return {}

    def convert(self, output_format="json", add_delving_fields=True):
        graph = self.bindings()._graph
        if output_format is 'xml':
            output = graph.serialize(format="xml").decode('utf-8')
            return output
        else:
            context_dict = {"{}".format(prefix): namespace for prefix, namespace in
                            graph.namespace_manager.namespaces()}
            output = graph.serialize(format='json-ld', context=context_dict).decode('utf-8')
        return json.loads(output)


class ICNConverter(BaseConverter):
    @staticmethod
    def query_key_replace_dict(reverse=False):
        replace_dict = {
            'icn_': 'nave_',
            'europeana_': 'edm_'
        }
        if reverse:
            replace_dict = {val: key for key, val in replace_dict.items()}
        return replace_dict

    def get_converter_key(self):
        return "icn"

    def get_namespace(self):
        return "http://www.icn.nl/schemas/icn/"

    def get_field_dict(self):
        mapping = {
            "icn_creatorYearOfBirth": "nave_creatorYearOfBirth",
            "icn_creatorYearOfDeath": "nave_creatorYearOfDeath",
            "icn_creatorRole": "nave_creatorRole",
            "icn_technique": "nave_technique",
            "icn_material": "nave_material",
            "icn_location": "nave_location",
            "icn_province": "nave_province",
            "icn_collectionPart": "nave_collectionPart",
            "icn_acquisitionMeans": "nave_acquisitionMeans",
            "icn_collectionType": "nave_collectionType",
            "icn_acquisitionYear": "nave_acquisitionYear",
            "icn_purchasePrice": "nave_purchasePrice",
            "icn_acquiredWithHelpFrom": "nave_acquiredWithHelpFrom",
            "icn_physicalState": "nave_physicalState",
            "icn_musipCollectionUri": "nave_musipCollectionUri",
            "icn_musipCollectionDisplayName": "nave_musipCollectionDisplayName",
            "icn_musipMuseumUri": "nave_musipMuseumUri",
            "icn_musipMuseumDisplayName": "nave_musipMuseumDisplayName",
            "icn_rijksCollection": "nave_rijksCollection",
            "icn_currentLocation": "nave_currentLocation",
            "icn_legalStatus": "nave_legalStatus",
            "icn_acceptedStateCharges": "nave_acceptedStateCharges",
            "icn_acceptedStateChargesReason": "nave_acceptedStateChargesReason",
            "icn_expulsionYear": "nave_expulsionYear",
            "icn_expulsionMeans": "nave_expulsionMeans",
        }
        return mapping


class ABMConverter(BaseConverter):
    @staticmethod
    def query_key_replace_dict(reverse=False):
        replace_dict = {
            'abm_': 'nave_',
            'europeana_': 'edm_'
        }
        if reverse:
            replace_dict = {val: key for key, val in replace_dict.items()}
        return replace_dict

    def get_converter_key(self):
        return "abm"

    def get_namespace(self):
        return "http://purl.org/abm/sen"

    def get_field_dict(self):
        mapping = {
            "abm_municipality": "nave_municipality",
            "abm_municipalityNr": "nave_municipalityNr",
            "abm_aboutPerson": "nave_aboutPerson",
            "abm_county": "nave_county",
            "abm_countyNr": "nave_countyNr",
            "abm_country": "nave_country",
            "abm_namedPlace": "nave_namedPlace",
            "abm_estateName": "nave_estateName",
            "abm_estateNr": "nave_estateNr",
            "abm_propertyName": "nave_propertyName",
            "abm_propertyNr": "nave_propertyNr",
            "abm_contentProvider": "nave_contentProvider",
            "abm_address": "nave_address",
            "abm_digitised": "nave_digitised",
            "abm_introduction": "nave_introduction",
            "abm_classification": "nave_classification",
            "abm_utm": "nave_utm",
            "abm_polygon_utm": "nave_polygon_utm",
            "abm_polygon_latLong": "nave_polygon_latLong",
            "abm_latLong": "nave_latLong",
            "abm_type": "nave_type",
            "abm_collectionType": "nave_collectionType",
            "abm_category": "nave_category",
            "abm_creatorUri": "nave_creatorUri",
            "abm_videoUri": "nave_videoUri",
            "abm_soundUri": "nave_soundUri",
            "abm_imageUri": "nave_imageUri",
            "abm_textUri": "nave_textUri",
        }
        return mapping
