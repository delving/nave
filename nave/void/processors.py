import json
import logging
import operator
from io import TextIOWrapper

from django.conf import settings
from django.utils.datastructures import MultiValueDict
from elasticsearch import helpers
from rdflib import Namespace, Graph, URIRef, Literal
from rdflib.namespace import RDF
from rdflib.plugins.parsers.ntriples import ParseError

from nave.lod.utils import rdfstore
from nave.lod.utils.resolver import RDFRecord
from nave.search.connector import get_es_client
from nave.void.models import DataSet

from nave.lod import tasks

logger = logging.getLogger(__name__)

CUSTOM_NS = Namespace(settings.RDF_SUPPORTED_PREFIXES.get('custom')[0])
EDM = Namespace('http://www.europeana.eu/schemas/edm/')
NAVE = Namespace('http://schemas.delving.eu/nave/terms/')
DELVING = Namespace('http://schemas.delving.eu/')

class IndexApiProcessor:
    """Process JSON from the index API and index as RDF in Elasticsearch.

    You can find more information on the Hub2 implementation here:
        https://github.com/delving/culture-hub/blob/1590d772d75bb6c004075af76e3653997fe2357d/modules/indexApi/app/controllers/api/Index.scala
        """

    def __init__(self, payload):
        self.payload = payload
        self.data = None

    def validate(self):
        """Validate the payload input."""
        try:
            self.data = json.loads(self.payload)
            return True, None
        except Exception as ex:
            return False, ex

    def get_delete_status(self, item):
        """Return delete status of the index item."""
        delete = item.get('@delete')
        return True if delete and delete.lower() == 'true' else False

    def create_hub_id(self, item):
        """Rerun hubId from index item."""
        return "{}_{}_{}".format(
            settings.ORG_ID,
            self.get_spec(item).lower(),
            self.get_local_id(item)
        )

    def get_spec(self, item):
        """Return spec from index item."""
        return item['@itemType'].lower()

    def get_doc_type(self, item):
        """Return the doctype for index items."""
        return 'indexitem'

    def get_record_type(self, item):
        """Return the record_type for Elasticsearch.  """
        return item['@itemType']

    def create_delete_action(self, item):
        """Create delete action for Elasticsearch bulk API."""
        return {
            '_op_type': 'delete',
            '_index': settings.SITE_NAME,
            '_type': self.get_doc_type(item),
            '_id': self.create_hub_id(item)
        }

    def get_local_id(self, item):
        """Get local identifier from index item."""
        return item['@itemId'].lower()

    def get_source_uri(self, item, as_uri=False):
        """Get the RDF source uri."""
        source_uri = 'http://{}/resource/{}/{}/{}'.format(
            settings.RDF_BASE_URL.replace('http://', ''),
            self.get_doc_type(item),
            self.get_spec(item).lower(),
            self.get_local_id(item)
        )
        if as_uri:
            source_uri = URIRef(source_uri)
        return source_uri

    def get_named_graph(self, item):
        """Get the Named Graph uri."""
        return '{}/graph'.format(self.get_source_uri(item).rstrip('/'))

    def process_field(self, field, system_field=False):
        """Process the field dictionary.

        Discard fields with empty '#text' values.
        """
        triples = []
        try:
            label = field['@name']
            text = field.get('#text')
            if not text:
                logger.warn('empty field: {}'.format(field))
                return None
            predicate = None
            if system_field:
                predicate = DELVING[label]
            elif ':' in label:
                ns_prefix, ns_label = label.split(':', maxsplit=1)
                if ns_prefix in ['europeana', 'edm', 'ese']:
                    namespace = EDM
                elif ns_prefix in ['delving', 'nave']:
                    namespace = NAVE
                else:
                    namespace = settings.RDF_SUPPORTED_PREFIXES.get(ns_prefix)
                    namespace = Namespace(namespace[0])
                if namespace:
                    predicate = namespace[ns_label]
                else:
                    logger.warn(
                        'Discarding because of unknown namespace: {}'.format(
                            ns_prefix
                        )
                    )
            else:
                predicate = CUSTOM_NS[label]
            # todo add switches for fieldType
            # string, location, int, single, text, date, link
            if not system_field:
                field_type = field.get('@fieldType')
                if field_type in ['link']:
                    obj = URIRef(text)
                elif field_type in ['location']:
                    obj = Literal(text)
                    triples.append(
                        (NAVE.geoHash, obj)
                    )
                # todo: support data after v2 internal storage is available
                else:
                    obj = Literal(text)
            else:
                obj = Literal(text)
            if predicate in [NAVE.resourceUri]:
                triples.append((EDM.object, obj))
            triples.append((predicate, obj))
            return triples
        except KeyError as ke:
            logger.warn('Invalid field labels: {}\n{}'.format(field, ke))
        return None

    def to_graph(self, item):
        """Convert the index item to an RDF graph."""
        named_graph = URIRef(self.get_named_graph(item))
        s = URIRef(self.get_source_uri(item))
        g = Graph(identifier=named_graph)
        g.add((s, RDF.type, CUSTOM_NS.IndexItem))
        if not 'field' in item:
            raise ValueError('"field" needs to exist and be a list.')
        extracted_fields = []
        for field in item['field']:
            extracted_field = self.process_field(field, system_field=False)
            if extracted_field:
                extracted_fields.extend(extracted_field)
        if 'systemField' in item:
            for field in item['systemField']:
                extracted_field = self.process_field(field, system_field=True)
                if extracted_field:
                    extracted_fields.extend(extracted_field)
        for field in extracted_fields:
            pred, obj = field
            g.add((s, pred, obj))
        return g

    def get_index_items(self):
        """Return a list of index items."""
        valid, exception = self.validate()
        if not valid:
            logger.warn('payload not valid: {}'.format(exception))
            raise exception
        if 'indexRequest' not in self.data:
            return []
        if 'indexItem' not in self.data['indexRequest']:
            return []
        index_items = self.data['indexRequest']['indexItem']
        if not isinstance(index_items, list):
            index_items = [index_items]
        return index_items

    def get_es_action(self, item):
        """Create a Bulk API es action from index item."""
        graph = self.to_graph(item)
        record = RDFRecord(
            hub_id=self.create_hub_id(item),
            source_uri=self.get_source_uri(item),
            named_graph_uri=self.get_named_graph(item),
            graph=graph,
            spec=self.get_spec(item).lower()
        )
        return record.create_es_action(
            doc_type=self.get_doc_type(item),
            record_type=self.get_record_type(item),
            context=False
        )

    def process(self, index=True):
        """Get a dict of index items by type."""
        total = 0
        indexed = 0
        deleted = 0
        invalid = 0
        invalid_items = []
        es_actions = []
        for item in self.get_index_items():
            try:
                total += 1
                delete = self.get_delete_status(item)
                if delete:
                    es_actions.append(self.create_delete_action(item))
                    deleted += 1
                else:
                    es_action = self.get_es_action(item)
                    es_actions.append(es_action)
                    indexed += 1
            except Exception as ex:
                logger.error(ex)
                invalid += 1
                invalid_items.append(item)
        if es_actions and index:
            nr, errors = helpers.bulk(
                get_es_client(),
                es_actions,
                raise_on_error=False
            )
            if nr > 0 and not errors:
                logger.info("Indexed records: {}".format(nr))
            elif errors:
                logger.warn(
                    "Something went wrong with bulk index: {}".format(errors)
                )
        return {
            'totalItemCount': total,
            'indexedItemCount': indexed,
            'deletedItemCount': deleted,
            'invalidItemCount': invalid,
            'invalidItems': invalid_items
        }


class BulkApiProcessor:

    def __init__(self, payload, store=None, force_insert=False):
        self.payload = payload
        self.store = rdfstore.get_rdfstore()
        self.rdf_errors = []
        self.index_errors = []
        self.store_errors = []
        self.json_errors = []
        self.es_actions = {}
        self.records_stored = 0
        self.records_already_stored = 0
        self.records_with_errors = 0
        self.sparql_update_queries = {}
        self.force_insert = force_insert
        self.api_requests = self._get_json_entries_from_payload()
        self.current_dataset = None
        self.spec = None

    def set_force_insert(self, force_insert):
        self.force_insert = force_insert

    def diff_by_content_hash(self):
        ids = [{"_id": key[0]} for key in self.es_actions.keys()]
        mget_ids = get_es_client().mget(
            body={"docs": ids},
            index=settings.SITE_NAME,
            _source_include=['system.content_hash']
        )
        index_sets = {
            (
                doc.get('_id'),
                doc['_source'].get('system', {'content_hash': None}).get('content_hash')) for doc in mget_ids.get('docs') if doc['found']}
        new_records = set(self.es_actions.keys()).difference(index_sets)
        self.records_stored = len(new_records)
        self.records_already_stored = len(ids) - self.records_stored
        es_actions = [es_action for k, es_action in self.es_actions.items() if k in new_records]
        sparql_updates = [sparql_update for k, sparql_update in self.sparql_update_queries.items() if k in new_records]
        return es_actions, sparql_updates

    def process(self):
        for i, action in enumerate(self.api_requests):
            self._process_action(action)
        if self.es_actions:
            es_actions, sparql_updates = self.diff_by_content_hash()
            self.bulk_index(es_actions)
            if sparql_updates and settings.RDF_STORE_TRIPLES:
                tasks.process_sparql_updates.apply_async(
                    (sparql_updates, None),
                    routing_key=settings.RECORD_QUEUE,
                    queue=settings.RECORD_QUEUE
                )

        logger.info("Done Processing with {} graphs from {}.".format(self.records_stored, len(self.api_requests)))
        return self._processing_statistics()

    def bulk_index(self, es_actions):
        logger.debug(self.es_actions)
        nr, errors = helpers.bulk(get_es_client(), es_actions)
        if nr > 0 and not errors:
            logger.info("Indexed records: {}".format(nr))
            return True
        elif errors:
            logger.warn("Something went wrong with bulk index: {}".format(errors))
            return False
        return False

    @staticmethod
    def synchronise_dataset_metadata(store, dataset_graph_uri):
        """Synchronise the metadata of the dataset between Narthex and Nave."""
        ds = DataSet.get_dataset_from_graph(dataset_graph_uri=dataset_graph_uri, store=store)
        ds.save()
        return ds

    def _process_action(self, action):
        try:
            self.spec = action['dataset']
            process_verb = action['action']
            record = None
            logger.info("Bulk API action: {} ({})".format(process_verb, self.spec))
            if process_verb in ['clear_orphans']:
                purge_date = action.get('modification_date')
                if purge_date:
                    orphans_removed = RDFRecord.remove_orphans(spec=self.spec, timestamp=purge_date)
                    logger.info("Deleted {} orphans for {} before {}".format(orphans_removed, self.spec, purge_date))
                    # print("Deleted {} orphans for {} before {}".format(orphans_removed, self.spec, purge_date))
            elif process_verb in ['disable_index']:
                RDFRecord.delete_from_index(self.spec)
                logger.info("Deleted dataset {} from index. ".format(self.spec))
                # print("Deleted dataset {} from index. ".format(self.spec))
            elif process_verb in ['drop_dataset']:
                RDFRecord.delete_from_index(self.spec)
                DataSet.objects.filter(spec=self.spec).delete()
                logger.info("Deleted dataset {} from index. ".format(self.spec))
                # print("Deleted dataset {} from index. ".format(self.spec))
            elif process_verb in ['index']:
                record_graph_uri = action['graphUri']
                graph_ntriples = action['graph']
                acceptance_mode = action.get('acceptanceMode', "false")
                acceptance = True if acceptance_mode is not None and acceptance_mode.lower() in ['true'] else False
                content_hash = action.get('contentHash', None)
                from nave.lod.utils.resolver import ElasticSearchRDFRecord
                record = ElasticSearchRDFRecord(spec=self.spec, rdf_string=graph_ntriples)
                try:
                    rdf_format = record.DEFAULT_RDF_FORMAT if "<rdf:RDF" not in graph_ntriples else "xml"
                    record.from_rdf_string(
                        rdf_string=graph_ntriples,
                        named_graph=record_graph_uri,
                        input_format=rdf_format
                    )
                except ParseError as e:
                    self.rdf_errors.append((e, action))
                    logger.error(e, action)
                    return None
                self.records_stored += 1
                self.es_actions[(record.hub_id, content_hash)] = record.create_es_action(
                        action=process_verb,
                        store=self.store,
                        context=True,
                        flat=True,
                        exclude_fields=None,
                        acceptance=acceptance,
                        doc_type="void_edmrecord",
                        record_type="mdr",
                        content_hash=content_hash
                        )
                if settings.RDF_STORE_TRIPLES:
                    self.sparql_update_queries[(record.hub_id, content_hash)] = record.create_sparql_update_query(acceptance=acceptance)
            return record
        except KeyError as ke:
            self.json_errors.append((ke, action))
            self.records_with_errors += 1
            return None

    @staticmethod
    def _create_dataset_uri(record_graph_uri):
        return "/".join(record_graph_uri.split('/')[:-2]).replace('aggregation', 'dataset') + "/graph"

    def _get_json_entries_from_payload(self):
        json_entries = []
        for line in self._get_lines_from_payload():
            try:
                json_entries.append(json.loads(line))
            except ValueError as ve:
                logger.error(line, ve)
                self.json_errors.append((ve, line))
        return sorted(json_entries, key=operator.itemgetter('dataset'))

    def _get_lines_from_payload(self):
        if isinstance(self.payload, bytes):
            return self.payload.decode('UTF-8').splitlines()
        elif isinstance(self.payload, MultiValueDict) and self.payload:
            return TextIOWrapper(list(self.payload.values())[0].file).readlines()
        elif isinstance(self.payload, TextIOWrapper):
            return self.payload.readlines()
        return None

    def _processing_statistics(self):
        return {
            'spec': self.spec,
            'total_received': len(self.api_requests),
            # 'rdf_errors': len(self.rdf_errors),
            # 'store_errors': self.records_with_errors,
            # 'json_errors': len(self.json_errors),
            # 'index_errors': len(self.index_errors),
            'content_hash_matches': self.records_already_stored,
            'records_stored': self.records_stored,
            # 'errors': {
            #
            # }
        }
