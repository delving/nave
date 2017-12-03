import geobuf as geobuf
from collections import OrderedDict, defaultdict
from datetime import datetime
import unicodedata

import geojson
import six
from django.conf import settings
from django.utils.encoding import smart_text
from django.utils.xmlutils import SimplerXMLGenerator
from rdflib import Graph
from rest_framework import renderers
from rest_framework.renderers import BaseRenderer
from six import StringIO

from fastkml import kml
from shapely.geometry import Point, LineString, Polygon

from geojson import Feature, FeatureCollection
from geojson import Point as GeoPoint

from nave.lod.utils.rdfstore import get_namespace_manager


class KMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML.
    """

    media_type = 'text/xml'
    format = 'kml'
    charset = 'utf-8'

    def render(self, data, media_type=None, renderer_context=None):
        k = kml.KML()
        ns = '{http://www.opengis.net/kml/2.2}'

        doc = kml.Document(ns)
        k.append(doc)

        folder = kml.Folder(ns, name=settings.ORG_ID, description="KML generated from query")
        doc.append(folder)

        def process_fields(fields):
            elements = []
            for key, v in fields.items():
                for item in v:
                    elements.append(kml.UntypedExtendedDataElement(name=key, value=str(item)))

            extended_data = kml.ExtendedData(ns, elements=elements)

            point_field = "delving_geohash" if "delving_geohash" in fields else "point"
            meta_dict = {
                    '_id': fields.get('delving_hubId'),
                    'point': fields.get(point_field),
                    'name': fields.get('dc_title'),
                    'description': fields.get('dc_description')
            }
            for key, val in meta_dict.items():
                if val and len(val) > 0:
                    meta_dict[key] = str(val[0])
                else:
                    meta_dict[key] = None
            p = kml.Placemark(
                ns,
                meta_dict.get('_id'),
                meta_dict.get('name'),
                meta_dict.get('description'),
                extended_data=extended_data)
            point = meta_dict.get('point')
            if point:
                lat, lon = point.split(',')
                p.geometry = Point(float(lon.strip()), float(lat.strip()))
            folder.append(p)
            return p

        if 'item' in data['result']:
            fields = data['result']['item']['fields']
            process_fields(fields)
        elif 'items' in data['result']:
            for item in data['result']['items']:
                fields = item['item']['fields']
                process_fields(fields)
        elif 'item' in data:
            fields = data['item']['fields']
            place_mark = process_fields(fields)
            return place_mark.to_string()
        return k.to_string()


class GeoJsonRenderer(renderers.BaseRenderer):
    media_type = 'application/json'
    format = 'geojson'

    def process_fields(self, _id, fields, features, doc_type=None):
        properties = defaultdict(list)
        for key, values in fields.items():
            if any(isinstance(val, datetime) for val in values):
                clean_values = []
                for val in values:
                    if isinstance(val, datetime):
                        clean_values.append(val.isoformat())
                    else:
                        clean_values.append(val)
            else:
                properties[key] = values
        if doc_type:
            properties['doc_type'] = doc_type
        point_field = "delving_geohash" if "delving_geohash" in fields else "point"
        meta_dict = {
            'point': fields.get(point_field),
            'name': fields.get('dc_title'),
            'description': fields.get('dc_description')
        }
        for key, val in meta_dict.items():
            if val and len(val) > 0:
                meta_dict[key] = str(val[0])
            else:
                meta_dict[key] = None
        point = meta_dict.get('point')
        if point:
            lat, lon = point.split(',')
            center_point = GeoPoint((float(lon.strip()), float(lat.strip())))
            feature = Feature(geometry=center_point, id=_id, properties=properties)
            features.append(feature)
            return feature
        return None

    def get_features(self, data):
        features = []

        if 'item' in data['result']:
            item = data['result']['item']
            doc_id = item["doc_id"]
            doc_type = item["doc_type"]
            fields = item['fields']
            self.process_fields(doc_id, fields, features, doc_type=doc_type)
        elif 'items' in data['result']:
            for item in data['result']['items']:
                doc_id = item['item']["doc_id"]
                doc_type = item['item']["doc_type"]
                fields = item['item']['fields']
                self.process_fields(doc_id, fields, features, doc_type=doc_type)
                # elif 'item' in data:
                #     fields = data['item']['fieilds']
                #     place_mark = process_fields(fields)
                #     return place_mark.to_string()
        return features

    def render(self, data, media_type=None, renderer_context=None):
        features = self.get_features(data=data)
        feature_collection = FeatureCollection(features=features)
        return geojson.dumps(feature_collection)


class GeoBufRenderer(GeoJsonRenderer):

    media_type = 'application/octet-stream'
    format = 'geobuf'

    def render(self, data, media_type=None, renderer_context=None):
        features = super(GeoBufRenderer, self).get_features(data)
        feature_collection = FeatureCollection(features=features)
        geojson_output = geojson.dumps(feature_collection)
        return geobuf.encode(feature_collection)  # GeoJSON or TopoJSON -> Geobuf string


class XMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML.
    """

    media_type = 'application/xml'
    format = 'xml'
    charset = 'utf-8'
    item_tag_name = 'list-item'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized XML.
        """
        if data is None:
            return ''

        stream = StringIO()

        xml = SimplerXMLGenerator(stream, encoding=self.charset)
        xml.startDocument()

        self._to_xml(xml, data)

        xml.endDocument()
        return stream.getvalue()

    def _get_namespace_prefix(self, search_label):
        if "_" in search_label:
            return search_label.split('_')[0]
        return None

    @staticmethod
    def _get_uri_from_search_label(search_label):
        if "_" in search_label:
            prefix, *label = search_label.split('_')
            uri = settings.RDF_SUPPORTED_PREFIXES.get(prefix, None)
            if uri:
                uri = uri[0].rstrip('/')
            else:
                return None
            return prefix, uri, "_".join(label)
        return None

    @staticmethod
    def normalize_attribute(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    @staticmethod
    def _create_inner_tag_name(key):
        return key.lower() if not key.endswith('s') else key.lower()[:-1]

    @staticmethod
    def remove_control_characters(s):
        return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

    def _to_xml(self, xml, data, tag_name=item_tag_name):
        if isinstance(data, (list, tuple)):
            for item in data:
                if tag_name == self.item_tag_name:
                    test = 1
                if tag_name is None:
                    self._to_xml(xml, item)
                elif isinstance(item, tuple):
                    search_label = item[0]
                    value = item[1]
                    if "_" in search_label:
                        prefix, ns, label = self._get_uri_from_search_label(search_label)
                        full_uri = ns, label
                        xml.startPrefixMapping(prefix, ns)
                        qname = search_label.replace('_', ":")
                        xml.startElementNS(full_uri, qname, {})
                        self._to_xml(xml, value)
                        xml.endElementNS(full_uri, qname)
                        xml.endPrefixMapping(prefix)
                elif tag_name in ['breadcrumb', 'link', 'facet']:
                    has_text = False
                    output = None
                    output_keys = [key for key in item.keys() if key in ['display', 'pageNumber', 'displayString']]
                    if output_keys:
                        for key in output_keys:
                            output = item.pop(key)
                    # Remove links from item dict
                    facet_links = None
                    if 'links' in item:
                        facet_links = item.pop('links')
                    # run with _to_xml
                    attr = {key: self.normalize_attribute(value) for key, value in item.items()}
                    xml.startElement(tag_name, attr)
                    if facet_links:
                        self._to_xml(xml, facet_links, tag_name="link")
                    else:
                        xml.characters(smart_text(output))
                    xml.endElement(tag_name)
                else:
                    xml.startElement(tag_name, {})
                    self._to_xml(xml, item)
                    xml.endElement(tag_name)
        elif isinstance(data, dict):
            for key, value in six.iteritems(data):
                # if value is ordered dict use key singular as list-item
                xml.startElement(key, {})
                if value and isinstance(value, list) and isinstance(value[0], OrderedDict):
                    tag_name = self._create_inner_tag_name(key)
                    if tag_name in ['item', 'field', 'relateditem'] and 'i18n' not in value[0].keys():
                        tag_name = None
                    self._to_xml(xml, value, tag_name=tag_name)
                elif isinstance(value, OrderedDict) and key in ['fields']:
                    tag_name = self._create_inner_tag_name(key)
                    new_list = []
                    for k, v in value.items():
                        if isinstance(v, list):
                            for entry in v:
                                new_list.append((k, entry))
                        else:
                            new_list.append((k, v))
                    self._to_xml(xml, new_list)
                    # xml.endElement(key)
                elif isinstance(value, OrderedDict) and key in ['field']:
                    tag_name = self._create_inner_tag_name(key)
                    self._to_xml(xml, value)
                elif isinstance(value, OrderedDict) and key in ['layout']:
                    tag_name = "fields"
                    modified_value = OrderedDict()
                    modified_value["fields"] = value['layout']
                    self._to_xml(xml, modified_value)
                elif isinstance(value, str) and tag_name in ["field", None]:
                    tag_name = None
                    self._to_xml(xml, value, tag_name=tag_name)
                else:
                    self._to_xml(xml, value)
                xml.endElement(key)

        elif data is None:
            # Don't output any value
            pass

        else:
            if isinstance(data, str):
                xml.characters(smart_text(self.remove_control_characters(data)))
            else:
                xml.characters(smart_text(data))


class RDFBaseRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'rdf'

    def render(self, data, media_type=None, renderer_context=None):
        g = Graph(namespace_manager=get_namespace_manager())
        g.parse(data=data, format='n3')
        return smart_text(g.serialize(format=self.format))


class JSONLDRenderer(RDFBaseRenderer):
    media_type = 'application/json'
    format = 'json-ld'


class RDFRenderer(RDFBaseRenderer):
    media_type = 'application/rdf+xml'
    format = 'rdf'

    def render(self, data, media_type=None, renderer_context=None):
        g = Graph()
        g.namespace_manager = get_namespace_manager()
        g.parse(data=data, format='n3')
        return smart_text(g.serialize(format='xml'))


class NTRIPLESRenderer(RDFBaseRenderer):
    media_type = 'text/plain'
    format = 'nt'


class TURTLERenderer(RDFBaseRenderer):
    media_type = 'text/turtle'
    format = 'turtle'


class N3Renderer(renderers.BaseRenderer):
    media_type = 'text/n3'
    format = 'n3'

    def render(self, data, media_type=None, renderer_context=None):
        return smart_text(data)
