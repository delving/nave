import logging
from collections import defaultdict
from datetime import time, datetime
from time import ctime, sleep

import os
import re

from django.conf import settings
from elasticsearch import helpers

from rdflib import Literal, URIRef, ConjunctiveGraph

from nave.lod.tasks import get_es
from nave.lod.utils import rdfstore
from nave.lod.utils.rdfstore import get_rdfstore
from nave.lod.utils.resolver import RDFRecord, GraphBindings

from nave.lod.utils.resolver import ElasticSearchRDFRecord

logger = logging.getLogger(__file__)


class NarthexBulkLoader:
    """
    Load EDM records processed by Narthex directly into Nave.
    """

    def __init__(
            self,
            org_id=settings.ORG_ID,
            index=settings.SITE_NAME,
            narthex_base="~/NarthexFiles"
        ):
        self._org_id = org_id
        self.narthex_base = narthex_base

    @staticmethod
    def is_line_marker(line):
        """Determine if line is the line marker between graphs.

        Narthex deliminates each graph stored in XML with a comment listing the named_graph and the content_hash.
        """
        m = re.match("<!--<(http://.*?graph)__(.*?)>-->", line)
        if not m:
            return False, None, None
        named_graph, content_hash = m.groups()
        return True, named_graph, content_hash

    @property
    def dataset_base_path(self):
        """Return the base path where the Narthex datasets are stored."""
        return os.path.join(os.path.expanduser(self.narthex_base), self._org_id, "datasets")

    def spec_processed_path(self, spec):
        """Return the path to the processed files for the spec."""
        return os.path.join(self.dataset_base_path, spec, "processed")

    def spec_processed_files(self, spec):
        """Return a list of processed files."""
        processed_dir = self.spec_processed_path(spec)
        if not os.path.exists(processed_dir):
            return []
        return [fname for fname in os.listdir(processed_dir) if fname.endswith(".xml")]

    def specs(self):
        """Returns a list of all specs stored by Narthex."""
        return [spec for spec in os.listdir(self.dataset_base_path) if
                os.path.isdir(os.path.join(self.dataset_base_path, spec))]

    def processable_files(self):
        """Returns a dict of all specs that have processed files."""
        processed_specs = defaultdict(list)
        for spec in self.specs():
            processed_specs[spec] = self.spec_processed_files(spec)
        return processed_specs

    def walk_all_datasets(self):
        """Traverse through all Narthex Datasets on disk and store the processed data in ElasticSearch."""
        processed_specs = {}
        for spec, processed_files in self.processable_files().items():
            total_lines = total_records = 0
            try:
                for fname in processed_files:
                    lines, records = self.process_narthex_file(
                        spec=spec,
                        path=os.path.join(self.spec_processed_path(spec), fname),
                        console=True,
                        index=self.index
                    )
                    total_lines += lines
                    total_records += records
                    processed_specs[spec] = (total_lines, total_records)
            except Exception as ex:
                print("Problem with spec {} and file {}, with error: \n {}".format(spec, fname, ex))
        return processed_specs

    def process_narthex_file(self, spec, store=None, acceptance=False, path=None, console=False, index=None):

        if not index and not self.index:
            index = settings.SITE_NAME

        start = datetime.now()

        if not store:
            store = rdfstore.get_rdfstore()

        if not path:
            processed_fname = self.get_narthex_processed_fname()
        else:
            processed_fname = path
        print("started processing {} for dataset {}".format(processed_fname, spec))

        with open(processed_fname, 'r') as f:
            rdf_record = []
            lines = 0
            records = 0
            stored = 0
            new = 0
            not_orphaned = []
            sparql_update_queries = []
            es_actions = []
            # set orphaned records

            for line in f:
                lines += 1
                exists, named_graph, content_hash = self.is_line_marker(line)
                if exists:
                    new += 1
                    records += 1
                    triples = " ".join(rdf_record)
                    record = ElasticSearchRDFRecord(rdf_string=triples, spec=spec)
                    try:
                        record.from_rdf_string(named_graph=named_graph, rdf_string=triples, input_format="xml")
                        es_actions.append(record.create_es_action(
                            doc_type="void_edmrecord",
                            record_type="mdr",
                            context=True,
                            index=index
                        ))
                    except Exception as ex:
                        if console:
                            print("problem with {} for spec {} caused by {}".format(triples, spec, ex))
                        else:
                            logger.error("problem with {} for spec {} caused by {}".format(triples, spec, ex))
                    rdf_record[:] = []
                    if settings.RDF_STORE_TRIPLES:
                        sparql_update_queries.append(
                            record.create_sparql_update_query(acceptance=acceptance)
                        )
                    nr_sparql_updates = len(sparql_update_queries)
                    if settings.RDF_STORE_TRIPLES and nr_sparql_updates > 0 and nr_sparql_updates % 50 == 0:
                        store.update("\n".join(sparql_update_queries))
                        sparql_update_queries[:] = []
                    if records % 100 == 0 and records > 0:
                        logger.info("processed {} records of {} at {}".format(records, spec, ctime()))
                        if console:
                            print("processed {} records of {} at {}".format(records, spec, ctime()))
                        if len(es_actions) > 100:
                            self.bulk_index(es_actions, spec)
                            es_actions[:] = []
                else:
                    rdf_record.append(line)
            # store the remaining bulk items
            self.bulk_index(es_actions, spec)
            if settings.RDF_STORE_TRIPLES and len(sparql_update_queries) > 0:
                store.update("\n".join(sparql_update_queries))
            logger.info(
                "Dataset {}: records inserted {}, records same content hash {}, lines parsed {}, total records processed {}".format(
                    spec, new, stored, lines, records)
            )
            print("Finished loading {spec} with {lines} and {records} in {seconds}\n".format(
                spec=spec,
                lines=lines,
                records=records,
                seconds=datetime.now() - start
            ))

            RDFRecord.remove_orphans(spec, start.isoformat())
            return lines, records

    ### old stuff

    def bulk_index(self, es_actions, spec):
        logger.debug(es_actions)
        nr, errors = helpers.bulk(get_es(), es_actions)
        if nr > 0 and not errors:
            logger.info("Indexed records {} for dataset {}".format(nr, spec))
            return True
        elif errors:
            logger.error("Something went wrong with bulk index: {}".format(errors))
            return False
        return False



    @staticmethod
    def add_triples(graph, subject, value_dict):
        for k, v in value_dict.items():
            obj = Literal(v)
            if v.startswith("http:"):
                obj = URIRef(v)
            graph.add((subject, URIRef(k), obj))
        return graph

    def create_actor_subject_uri(self, actor_name, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        return URIRef("{}/resource/actor/{}".format(base_url.rstrip('/'), actor_name))

    def create_actor(self, actor_name, base_url=None,
                     named_graph="http://schemas.delving.eu/narthex/terms/Actors/graph"):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        g = ConjunctiveGraph(identifier=URIRef(named_graph))
        subject = self.create_actor_subject_uri(actor_name)
        values = {
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://schemas.delving.eu/narthex/terms/Actor",
            "http://schemas.delving.eu/narthex/terms/username": actor_name,
            "http://schemas.delving.eu/narthex/terms/passwordHash": "c66ed5e2e6a32fa384176805f380bd77924f2c76aff2a2dcb6429367a14d1e74",
        }
        self.add_triples(g, subject, values)
        return g

    def create_dataset_subject_uri(self, spec, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        return URIRef("{}/resource/dataset/{}".format(base_url, spec))

    def create_dataset(self, spec, actor, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        subject = self.create_actor_subject_uri(spec, base_url=base_url)
        named_graph = subject + "/graph"
        actor_subject = self.create_actor_subject_uri(actor, base_url=base_url)
        g = ConjunctiveGraph(identifier=named_graph)
        values = {
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://schemas.delving.eu/narthex/terms/Dataset",
            "http://schemas.delving.eu/narthex/terms/acceptanceMode": "false",
            "http://schemas.delving.eu/narthex/terms/acceptanceOnly": "true",
            "http://schemas.delving.eu/narthex/terms/actorOwner": str(actor_subject),
            "http://schemas.delving.eu/narthex/terms/datasetCharacter": "character-mapped",
            "http://schemas.delving.eu/narthex/terms/datasetMapToPrefix": "edm",
            "http://schemas.delving.eu/narthex/terms/datasetSpec": spec,
            "http://schemas.delving.eu/narthex/terms/publishIndex": "true",
            "http://schemas.delving.eu/narthex/terms/publishLOD": "true",
            "http://schemas.delving.eu/narthex/terms/publishOAIPMH": "true",
            "http://schemas.delving.eu/narthex/terms/synced": "false",
            "http://schemas.delving.eu/narthex/terms/datasetName": spec,
            "http://schemas.delving.eu/narthex/terms/datasetDescription": spec,
            "http://schemas.delving.eu/narthex/terms/datasetAggregator": "{} Aggregator".format(spec),
            "http://schemas.delving.eu/narthex/terms/datasetOwner": "{} Owner".format(spec),
            "http://schemas.delving.eu/narthex/terms/datasetLanguage": "NL",
            "http://schemas.delving.eu/narthex/terms/datasetRights": "http://creativecommons.org/publicdomain/mark/1.0/",
        }
        self.add_triples(g, subject, values)
        return g

    def store_ds(self, spec, actor, base_url=None):
        # TODO fix this so new datasets can be created this way
        if not base_url:
            base_url = settings.RDF_BASE_URL
        store = get_rdfstore().get_graph_store
        actor_graph = self.create_actor(actor_name=actor)
        result = store.post(str(actor_graph.identifier), data=actor_graph)
        if not result:
            raise Exception()
        dataset_graph = self.create_dataset(spec, actor, base_url)
        result = store.put(str(dataset_graph.identifier), data=dataset_graph)
        if not result:
            raise Exception()

    def parse_narthex_xml(self, actor, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        ds = DataSet.objects.filter(spec=self.spec)
        graph_name = self.create_dataset_subject_uri(self.spec, base_url) + "/graph"
        if not ds:
            self.store_ds(self.spec, actor, base_url)
            ds = DataSet.get_dataset_from_graph(dataset_graph_uri=str(graph_name))
        else:
            ds = ds.first()
        return ds.process_narthex_file(path=self.path, console=True)
