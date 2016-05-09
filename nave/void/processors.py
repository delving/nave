import json
import logging
import operator
from io import TextIOWrapper

from django.apps import apps
from django.conf import settings
from django.utils.datastructures import MultiValueDict
from elasticsearch import helpers
from rdflib import ConjunctiveGraph
from rdflib.plugins.parsers.ntriples import ParseError

from lod.utils import rdfstore
from void import get_es
from void.models import DataSet

logger = logging.getLogger(__name__)


class BulkApiProcessor:

    def __init__(self, payload, store=None, force_insert=False):
        self.payload = payload
        self.store = rdfstore.get_rdfstore()
        self.rdf_errors = []
        self.index_errors = []
        self.store_errors = []
        self.json_errors = []
        self.es_actions = []
        self.records_stored = 0
        self.records_already_stored = 0
        self.records_with_errors = 0
        self.sparql_update_queries = []
        self.rdf_graphs = []
        self.force_insert = force_insert
        self.api_requests = self._get_json_entries_from_payload()
        self.current_dataset = None
        self.spec = None

    def set_force_insert(self, force_insert):
        self.force_insert = force_insert

    def process(self):
        for i, action in enumerate(self.api_requests):
            self._process_action(action)
        if self.es_actions:
            self.bulk_index()
        # todo: hand off the rdf syncing to other celery async task
        if self.sparql_update_queries and settings.RDF_STORE_TRIPLES:
            # tasks.store_graphs.starmap(self.rdf_graphs).apply_async(
            #     routing_key=settings.RECORD_QUEUE,
            #     queue=settings.RECORD_QUEUE
            # )
            self.store.update("\n".join(self.sparql_update_queries))

        logger.info("Done Processing with {} graphs from {}.".format(self.records_stored, len(self.api_requests)))
        return self._processing_statistics()

    def bulk_index(self):
        logger.debug(self.es_actions)
        nr, errors = helpers.bulk(get_es(), self.es_actions)
        if nr > 0 and not errors:
            logger.info("Indexed records: {}".format(nr))
            return True
        elif errors:
            logger.error("Something went wrong with bulk index: {}".format(errors))
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
            record_graph_uri = action['graphUri']
            graph_ntriples = action['graph']
            process_verb = action['action']
            acceptance_mode = action.get('acceptanceMode', "false")
            acceptance = True if acceptance_mode is not None and acceptance_mode.lower() in ['true'] else False
            content_hash = action.get('contentHash', None)
            try:
                graph = ConjunctiveGraph(identifier=record_graph_uri)
                rdf_format = "nt" if "<rdf:RDF" not in graph_ntriples else "xml"
                graph.parse(data=graph_ntriples, format=rdf_format)
            except ParseError as e:
                self.rdf_errors.append((e, action))
                logger.error(e, action)
                return None
            if self.current_dataset is None or self.current_dataset.spec is not self.spec:
                try:
                    self.current_dataset = DataSet.objects.get(spec=self.spec)
                except DataSet.DoesNotExist as dne:
                    logger.warn(dne)
                    self.current_dataset = self.synchronise_dataset_metadata(
                        store=self.store,
                        dataset_graph_uri=self._create_dataset_uri(record_graph_uri)
                    )
            app, model = action['type'].split('_')
            action_model = apps.get_model(app_label=app, model_name=model)
            record = action_model.graph_to_record(graph=graph,
                                                  bulk=True,
                                                  ds=self.current_dataset,
                                                  content_hash=content_hash,
                                                  force_insert=self.force_insert,
                                                  acceptance=acceptance
                                                  )
            if record is None:
                self.records_already_stored += 1
                return None
            self.records_stored += 1
            self.es_actions.append(
                record.create_es_action(
                    action=process_verb,
                    store=self.store,
                    context=False,  # todo: fix issue with context indexing later
                    flat=True,
                    exclude_fields=None,
                    acceptance=acceptance
                )
            )
            self.rdf_graphs.append(record.get_triples(acceptance=acceptance))
            if settings.RDF_STORE_TRIPLES:
                self.sparql_update_queries.append(record.create_sparql_update_query(acceptance=acceptance))
            if action in ['clear_orphans']:
                # todo: implement orphan clear out with RDFRecord
                pass
            return record
            # if process_verb in ['index', 'delete']:
            #     self.es_actions.append(
            #         record.create_es_action(
            #             action=process_verb,
            #             store=self.store,
            #             context=False,  # todo: fix issue with context indexing later
            #             flat=True,
            #             exclude_fields=None
            #         )
            #     )
            # if not settings.RDF_USE_LOCAL_GRAPH:
            #     if process_verb in ['store', 'index', 'delete']:
            #         deleted = process_verb == 'delete'
            #         self.sparql_update_queries.append(record.create_sparql_update_query(delete=deleted))

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
            'rdf_errors': len(self.rdf_errors),
            'store_errors': self.records_with_errors,
            'json_errors': len(self.json_errors),
            'index_errors': len(self.index_errors),
            # 'content_hash_matches': self.records_already_stored,
            'records_stored': self.records_stored,
            # 'errors': {
            #
            # }
        }
