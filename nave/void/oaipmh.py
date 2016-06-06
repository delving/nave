# -*- coding: utf-8 -*- 
"""

"""
from collections import defaultdict, namedtuple
from enum import Enum

import os
import requests
from dateutil import parser
from django.conf import settings
from django.views.generic import TemplateView
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, A, Q
from lxml import etree as ET

from lod.utils.resolver import RDFRecord, ElasticSearchRDFRecord
from void import REGISTERED_CONVERTERS
from void.models import DataSet, OaiPmhPublished, EDMRecord


class OaiVerb(Enum):
    Identify = 1
    ListIdentifiers = 2
    GetRecord = 3
    ListMetadataFormats = 4
    ListRecords = 5
    ListSets = 6


class OaiParam(Enum):
    verb = 1
    from_ = 2
    to = 3
    identifier = 4
    set = 5
    metadataPrefix = 6
    resumptionToken = 7
    until = 8


VERBS_WITH_PARAMS = {
    OaiVerb.Identify: [OaiParam.verb],
    OaiVerb.ListIdentifiers: [OaiParam.verb, OaiParam.resumptionToken, OaiParam.from_,
                              OaiParam.to, OaiParam.set, OaiParam.metadataPrefix],
    OaiVerb.GetRecord: [OaiParam.verb, OaiParam.identifier, OaiParam.metadataPrefix],
    OaiVerb.ListMetadataFormats: [OaiParam.verb],
    OaiVerb.ListRecords: [OaiParam.verb, OaiParam.resumptionToken, OaiParam.from_,
                          OaiParam.to, OaiParam.set, OaiParam.metadataPrefix],
    OaiVerb.ListSets: [OaiParam.verb]
}

PARAMS_WITH_VERBS = defaultdict(list)

for verb, params in list(VERBS_WITH_PARAMS.items()):
    for param in params:
        PARAMS_WITH_VERBS[param].append(verb)

class OAIException(Exception):

    def __init__(self, code, message, *args, **kwargs): # real signature unknown
        self.message = message
        self.code = code


class OAIProvider(TemplateView):
    content_type = 'application/xml'
    oai_identifier_field = 'hub_id'
    set_field = 'dataset__spec'
    dataset_model = DataSet
    dataset_access_filter = {'oai_pmh': OaiPmhPublished.public}
    dataset_search_key = 'dataset__spec'
    record_model = EDMRecord
    record_access_filter = {'dataset__oai_pmh': OaiPmhPublished.public}
    records_returned = 100

    def __init__(self, **kwargs):
        super(OAIProvider, self).__init__(**kwargs)
        self.request = None
        self.oai_verb = None
        self.params = None
        self.metadataPrefix = "edm-strict"
        self.cursor = 0
        self.filters = None
        self.list_size = None
        self.set = None

    class Meta:
        abstract = True

    def get_dataset_list(self):
        """
        The list of datasets that are publicly available.

        This can be either a fixed list or a database query
        :return: Tuple list of spec and description of the datasets
        """
        raise NotImplementedError("implement me")

    def get_items(self):
        raise NotImplementedError("implement me")

    def get_list_size(self):
        raise NotImplementedError("implement me")

    def items(self):
        """Return QuerySet with the filters from request applied."""
        if not self.list_size:
            self.list_size = self.get_list_size()
        objects = self.get_items()
        if not objects:
            raise OAIException(
                code="noRecordsMatch",
                message="The combination of the values of the from, until, set and metadataPrefix "
                        "arguments results in an empty list."
            )
        return objects

    def get_item(self, identifier):
        raise NotImplementedError("implement me")

    def item(self):
        self.template_name = "oaipmh/get_record.xml"
        identifier = self.request.GET.get('identifier')
        if not identifier:
            return self.error(
                "badArgument",
                "The request includes illegal arguments or is missing required arguments."
            )
        items = [self.get_item(identifier)]
        if not items:
            return self.error(
                "idDoesNotExist",
                "The value of the identifier argument is unknown or illegal in this repository."
            )
        converters = REGISTERED_CONVERTERS
        current_converter = converters[self.metadataPrefix]
        converted_items = []
        for i in list(items):
            converted_items.append(self._get_item_info(item=i, converter=current_converter))
        return self.render_to_response({
            'items': converted_items
        })

    def last_modified(self, obj):
        # datetime object was last modified
        raise NotImplementedError("Implement me")

    def oai_identifier(self, obj):
        # oai identifier for a given object
        return getattr(obj, self.oai_identifier_field)

    def sets(self, obj):
        # the sets a given object belongs to
        nesting = self.set_field.split('__')
        return getattr(getattr(obj, nesting[0]), nesting[1])

    def render_to_response(self, context, **response_kwargs):
        # all OAI responses should be xml
        if 'content_type' not in response_kwargs:
            response_kwargs['content_type'] = self.content_type

        # add common context data needed for all responses
        context.update({
            'verb': self.oai_verb,
            'all_params': " ".join(["{}=\"{}\"".format(key, value) for key, value in self.request.GET.dict().items()]),
            'url': self.request.build_absolute_uri(self.request.path),
        })
        return super(TemplateView, self) \
            .render_to_response(context, **response_kwargs)

    def identify(self):
        """Return the OAI-PMH Identify request.

        See http://www.openarchives.org/OAI/openarchivesprotocol.html#Identify
        """
        self.template_name = 'oaipmh/identify.xml'
        identify_data = {
            'name': 'OAI-PMH repository for {}'.format(settings.SITE_NAME),
            # perhaps an oai_admins method with default logic settings.admins?
            'admins': (email for name, email in settings.ADMINS),
            'earliest_date': '1990-02-01T12:00:00Z',  # placeholder
            # should probably be a class variable/configuration
            'deleted': 'no',  # no, transient, persistent (?)
            # class-level variable/configuration (may affect templates also)
            'granularity': 'YYYY-MM-DDThh:mm:ssZ',  # or YYYY-MM-DD
            # class-level config?
            'compression': 'deflate',  # gzip?  - optional
            # description - optional
            # (place-holder values from OAI docs example)
            'identifier_scheme': 'oai',
            'repository_identifier': "{}".format(RDFRecord.get_rdf_base_url(prepend_scheme=True)),
            'identifier_delimiter': '_',
            'sample_identifier': '{}_spec_localId'.format(settings.SITE_NAME)
        }
        return self.render_to_response(identify_data)

    def list_datasets(self):
        """List all datasets that are marked as public and OAI-PMH harvestable."""
        self.template_name = 'oaipmh/list_datasets.xml'
        return self.render_to_response({'datasets': self.get_dataset_list()})

    def list_identifiers(self):
        self.template_name = 'oaipmh/list_identifiers.xml'
        identifiers = []
        for i in list(self.items()):
            item_info = {
                'identifier': self.oai_identifier(i),
                'last_modified': self.last_modified(i),
                'sets': None  # todo: implement sets later [self.sets(i)]
            }
            identifiers.append(item_info)
        return self.render_to_response({
            'items': identifiers,
            'resumption_token': self.generate_resumption_token(),
            'cursor': self.cursor,
            'list_size': self.list_size}
        )

    def list_metadata_formats(self):
        """ List supported graph converters. """
        self.template_name = "oaipmh/list_metadataformats.xml"
        converters = REGISTERED_CONVERTERS
        converter_list = [(converter().get_converter_key(), converter().get_namespace()) for key, converter in
                          converters.items() if key not in ['raw']]
        converter_list.append(('oai_dc', "http://www.openarchives.org/OAI/2.0/oai_dc/"))
        return self.render_to_response({
            "items": converter_list
        })

    def _get_item_info(self, item, converter):
        converter = converter(about_uri=item.document_uri, graph=item.get_graph())
        converted_fields = None
        record = None
        if not self.metadataPrefix.startswith("edm"):
            converted_fields = converter.convert(add_delving_fields=False)
            converted_fields.default_factory = None
            converted_fields = {key.replace("_", ":"): value for key, value in converted_fields.items()}
            namespaces = converter.get_namespaces(as_ns_declaration=True)
        else:
            record = converter.convert(add_delving_fields=False, output_format='xml')
            if isinstance(record, bytes):
                record = record.decode()
            record = record.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '')
            namespaces = converter.get_namespaces(as_ns_declaration=True)
        item_info = {
            'identifier': self.oai_identifier(item),
            'last_modified': self.last_modified(item),
            'sets': [],  # [self.sets(item)], todo implement later
            'fields': converted_fields,
            'record': record,
            'ns': namespaces
        }
        return item_info

    def list_records(self):
        self.template_name = "oaipmh/list_records.xml"
        items = []
        converters = REGISTERED_CONVERTERS
        current_converter = converters[self.metadataPrefix]
        for i in list(self.items()):
            items.append(self._get_item_info(i, current_converter))
        return self.render_to_response({
            'items': items,
            'resumption_token': self.generate_resumption_token(),
            'cursor': self.cursor,
            'list_size': self.list_size}
        )

    def error(self, code, text):
        # TODO: HTTP error response code? maybe 400 bad request?
        # NOTE: may need to revise, could have multiple error codes/messages
        self.template_name = 'oaipmh/error.xml'
        return self.render_to_response({
            'error_code': code,
            'error': text,
        })

    def get_next_cursor(self):
        return self.cursor + self.records_returned

    def generate_resumption_token(self):
        if self.cursor + self.records_returned >= self.list_size:
            return None
        token_dict = {'prefix': self.metadataPrefix, 'cursor': self.cursor + self.records_returned,
                      'list_size': self.list_size}
        token_dict.update(**self.filters)
        token_dict.pop(list(self.record_access_filter.keys())[0])
        return "::".join(["{}={}".format(key, value) for key, value in list(token_dict.items())])

    def create_filters_from_token(self, token):
        filters = dict([entry.strip().split('=') for entry in token.strip().split("::")])
        filters.update(self.record_access_filter)
        self.metadataPrefix = filters.pop('prefix')
        self.list_size = int(filters.pop('list_size'))
        self.cursor = int(filters.pop('cursor'))
        self.filters = filters
        return filters

    def create_harvest_steps(self, request):
        if not self.params:
            self._setup_request(request)
        if 'resumptionToken' in self.params:
            token = self.params.get('resumptionToken')
            self.create_filters_from_token(token)
        else:
            if 'metadataPrefix' in self.params:
                self.metadataPrefix = self.params.pop('metadataPrefix')
                if self.metadataPrefix in ['oai_dc']:
                    self.metadataPrefix = 'ese'
            if self.oai_verb.startswith('List'):
                filters = self.params.copy()
                # rename set to spec
                if self.oai_verb not in ["ListSets", "ListMetadataFormats"]:
                    filters[self.dataset_search_key] = filters.pop('set')
                if 'from' in filters:
                    filters["modified__gt"] = parser.parse(timestr=filters.pop('from'))
                if 'until' in filters:
                    filters["modified__lt"] = parser.parse(filters.pop('until'))
                filters.update(self.record_access_filter)
                self.filters = filters

    def _setup_request(self, request):
        self.request = request
        self.params = request.GET.dict()
        self.oai_verb = self.params.pop('verb') if 'verb' in self.params else None
        return self

    def get(self, request, *args, **kwargs):
        self._setup_request(request)
        allowed_params = [query_param.rstrip('_') for query_param in OaiParam._member_names_]

        for query_param in self.params.keys():
            if query_param not in allowed_params:
                return self.error(
                        code="badArgument",
                        text="""The request includes illegal arguments, is missing required arguments, includes a
                        repeated argument, or values for arguments have an illegal syntax.""",
                )

        if not self.oai_verb:
            return self.error(
                    code="badArgument",
                    text="""The request includes illegal arguments, is missing required arguments, includes a
                        repeated argument, or values for arguments have an illegal syntax.""",
            )

        self.create_harvest_steps(request)

        if self.metadataPrefix not in REGISTERED_CONVERTERS.keys():
            return self.error(
                code="cannotDisseminateFormat",
                text="The metadata format identified by the value '{}' given for the metadataPrefix argument is not "
                     "supported by the item or by the repository.".format(self.metadataPrefix)
            )

        verb_dict = {
            'Identify': self.identify,
            'ListIdentifiers': self.list_identifiers,
            'GetRecord': self.item,
            'ListMetadataFormats': self.list_metadata_formats,
            'ListRecords': self.list_records,
            'ListSets': self.list_datasets
        }

        try:
            return verb_dict[self.oai_verb]()
        except OAIException as oe:
            return self.error(oe.code, oe.message)
        except KeyError as ke:
            if self.oai_verb is None:
                error_msg = 'The request did not provide any verb.'
            else:
                error_msg = 'The verb "{}" is illegal'.format(self.oai_verb)
            return self.error('badVerb', error_msg)


class ElasticSearchOAIProvider(OAIProvider):
    client = Elasticsearch()
    ESDataSet = namedtuple("DataSet", ['spec', 'description', 'name', 'valid', 'data_owner'])
    _es_response = None

    def __init__(self, spec=None, query=None, **kwargs):
        super(ElasticSearchOAIProvider, self).__init__(**kwargs)
        self.query = query
        self.spec = spec

    def get_query_result(self):
        if not self._es_response:
            s = self.convert_filters_to_query(self.filters)
            self._es_response = s.execute()
        return self._es_response

    def get_list_size(self):
        return self.get_query_result().hits.total

    def get_items(self):
        if self.get_list_size() == 0:
            return None
        return ElasticSearchRDFRecord.get_rdf_records_from_query(
            query=self.convert_filters_to_query(self.filters),
            response=self.get_query_result()
        )

    def get_item(self, identifier):
        s = Search(using=self.client)
        s = s.query("match", **{"_id": identifier})
        response = s.execute()
        if response.hits.total != 1:
            return None
        return ElasticSearchRDFRecord.get_rdf_records_from_query(
            query=s,
            response=response)[0]

    def convert_filters_to_query(self, filters):
        s = Search(using=self.client)
        spec = filters.get("dataset__spec", None)
        modified_from = filters.get('modified__gt', None)
        modified_until = filters.get('modified__lt', None)
        if self.spec:
            spec = self.spec
        if self.query:
            s = s.query(self.query.get('filter'))
        elif spec:
            s = s.query("match", **{'system.spec.raw': spec})
        if modified_from:
            s = s.filter("range", **{"system.modified_at": {"gte": modified_from}})
        if modified_until:
            s = s.filter("range", **{"system.modified_at": {"lte": modified_until}})
        s = s.sort({"system.modified_at": {"order": "asc"}})
        return s[self.cursor: self.get_next_cursor()]

    def get_dataset_list(self):
        s = Search(using=self.client)
        datasets = A("terms", field="delving_spec.raw")
        if self.query:
            s = s.filter(self.query.get('filter'))
        elif self.spec:
            s = s.query("match", **{'system.spec.raw': self.spec})
        s.aggs.bucket("dataset-list", datasets)
        response = s.execute()
        specs = response.aggregations['dataset-list'].buckets
        return [self.ESDataSet(spec.key, None, None, spec.doc_count, None) for spec in specs]

    def last_modified(self, obj):
        return obj.last_modified()


class DjangoOAIProvider(OAIProvider):

    def get_list_size(self):
        return self.record_model.objects.filter(**self.filters).count()

    def get_items(self):
        objects = self.record_model.objects.filter(**self.filters).order_by('modified')
        if not objects:
            return None
        return objects[self.cursor:self.get_next_cursor()]

    def get_item(self, identifier):
        return self.record_model.objects.get(hub_id=identifier)

    def get_dataset_list(self):
        query_set = self.dataset_model.objects.filter(**self.dataset_access_filter)
        return query_set

    def last_modified(self, obj):
        return obj.modified


HarvestStep = namedtuple('HarvestStep', ['records_returned', 'total_records', 'resumption_token', 'records'])
HarvestRequest = namedtuple('HarvestRequest', ['base_url', 'set_spec', 'metadata_prefix', 'verb'])


class OAIHarvester:

    def __init__(self, base_url):
        self.base_url = base_url

    @staticmethod
    def get_next_oai_pmh_uri(harvest_request, harvest_step):
        uri = ""
        if harvest_step.total_records is 0:
            uri = "{0}?verb={1}".format(harvest_request.base_url, harvest_request.verb)
            if harvest_request.set_spec is not "":
                uri += "&set={}".format(harvest_request.set_spec)
            if harvest_request.metadata_prefix is not "":
                uri += "&metadataPrefix={}".format(harvest_request.metadata_prefix)
        else:
            uri = "{}?verb={}&resumptionToken={}".format(
                harvest_request.base_url,
                harvest_request.verb,
                harvest_step.resumption_token
            )
        return uri

    @staticmethod
    def clean_bad_namespaces(tn):
        from io import StringIO
        lines = tn.splitlines(True) # keep \n
        o = StringIO()
        for line in lines:
            if '<openskos:status>approved</openskos:status>' in line:
                line = line.replace('<openskos:status>approved</openskos:status>', '')
            o.write(line)
        return o

    @staticmethod
    def clean_response(response):
        clean_response = response.replace('<openskos:status>approved</openskos:status>', '')
        clean_response = clean_response.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
        return clean_response

    def parse_oai_pmh_response(self, harvest_request, harvest_step):
        records_processed = 0
        uri = self.get_next_oai_pmh_uri(harvest_request, harvest_step)
        response = requests.get(uri)
        print("'{}'".format(uri))
        resumption_token = None
        record_tree = ET.fromstring(self.clean_response(response.text))
        record_sep = '{http://www.openarchives.org/OAI/2.0/}record' if harvest_request.verb == "ListRecords" \
            else '{http://www.openarchives.org/OAI/2.0/}header'
        for record in record_tree.iter(record_sep):
            harvest_step.records.append(record)
            records_processed += 1
        token =  next(record_tree.iter('{http://www.openarchives.org/OAI/2.0/}resumptionToken'), None)
        if token.text is not None:
            resumption_token = token.text.strip()
            cursor = token.attrib.get('cursor')
            list_size = token.attrib.get('completeListSize')
        if records_processed == 0:
            with open('/tmp/test_output.xml', 'w') as f:
                f.write(response.text)
        print("token: {}/{}".format(resumption_token, records_processed))
        return HarvestStep(
            records_processed,
            harvest_step.total_records + records_processed,
            resumption_token,
            harvest_step.records
        )

    def get_records_from_oai_pmh(self, set_spec, metadata_prefix, verb="ListRecords"):
        harvest_step = HarvestStep(50, 0, "fake_token", ET.Element("delving-records"))
        harvest_request = HarvestRequest(self.base_url.rstrip("?"), set_spec, metadata_prefix, verb)
        print(harvest_request)
        while harvest_step.resumption_token is not None:
            harvest_step = self.parse_oai_pmh_response(harvest_request, harvest_step)
        tree = ET.ElementTree(harvest_step.records)
        output_file = os.path.join('/tmp', 'oai_records_{}_{}.xml'.format(set_spec, metadata_prefix))
        tree.write(output_file, encoding="utf-8", xml_declaration=True, pretty_print=True)
        print("processed {} records".format(harvest_step.total_records))
        return output_file
