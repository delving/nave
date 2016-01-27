# -*- coding: utf-8 -*- 
"""This module does contains the synchronisation tasks that keep the
metadata records stored in RDF store by Narthex in sync with the the Nave
database and search index.

To see how Narthex stores everything:

https://github.com/delving/narthex/blob/master/app/triplestore/Sparql.scala
https://github.com/delving/narthex/blob/master/app/dataset/ProcessedRepo.scala#L41


Workflow:

    *  synchronise datasets with Django Data model

"""
import re
import socket
import uuid
from urllib.error import URLError

from celery import shared_task, task, chain
from celery.utils.log import get_task_logger
from django.conf import settings
from elasticsearch import helpers

from lod.models import RDFModel
from lod.utils import rdfstore
from lod.utils.rdfstore import QueryType
from void import get_es
from void.models import DataSet, EDMRecord, DataSetType, OaiPmhPublished
from void.processors import BulkApiProcessor

logger = get_task_logger(__name__)
########################### Bulk API ##############################


def get_index_name(acceptance=False):
    return settings.SITE_NAME if not acceptance else "{}_acceptance".format(settings.SITE_NAME)


@task(bind=True, default_retry_delay=300, max_retries=5)
def process_bulk_api_request(self, request_payload):
    try:
        processor = BulkApiProcessor(request_payload)
        return processor.process()
    except URLError as ue:
        self.retry(ue)
    except socket.timeout as to:
        self.retry(to)
    except socket.error as err:
        self.retry(err)


# ########################### Datasets #############################
def find_datasets_by_sync_or_deleted_status(store, synced=None, deleted=None):
    """Find the list of datasets in the triple store which are out of sync with the database.

    This query takes not into account if the records or SKOS mappings that belong to this Dataset are out of sync.
    """
    triples = []
    if synced:
        triples.append("; <http://schemas.delving.eu/narthex/terms/synced> {sync_status}".format(sync_status=synced))
    if deleted:
        triples.append("; <http://schemas.delving.eu/narthex/terms/deleted> {sync_status}".format(sync_status=deleted))

    query = """
    REDUCED ?ds
    WHERE
    {{
     ?ds <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schemas.delving.eu/narthex/terms/Dataset>
     {check_status} .
    }}
    limit 50
    """.format(check_status="\n".join(triples))
    res = store.select(query=query)
    ds_list = {graph['ds']['value'] for graph in res['results']['bindings']}
    return len(ds_list), ds_list


@shared_task
def synchronise_datasets(store):
    """Find out of sync datasets and synchronise their content."""
    nr_out_of_sync, datasets_uris = find_datasets_by_sync_or_deleted_status(store, synced=False)
    if nr_out_of_sync == 0:
        logger.info("No datasets out of sync.")
        return 0
    for dataset_uri in datasets_uris:
        synchronise_dataset_metadata(store, dataset_uri)
    update_switch = [QueryType.remove_insert.format(
        named_graph="{}/graph".format(g.rstrip('/')),
        remove="?s <http://schemas.delving.eu/narthex/terms/synced> false",
        insert="?s <http://schemas.delving.eu/narthex/terms/synced> true"
    ) for g in datasets_uris]
    response = store.update(query="\n".join(update_switch))
    logger.info("Synchronised {} datasets: {}".format(nr_out_of_sync, dataset_uri))
    return nr_out_of_sync


def synchronise_dataset_metadata(store, dataset_graph_uri):
    """Synchronise the metadata of the dataset between Narthex and Nave."""
    ds = DataSet.get_dataset_from_graph(dataset_graph_uri=dataset_graph_uri, store=store)
    ds.save()
    return ds


@shared_task()
def delete_dataset_with_all_triples(ds, store, dataset_delete=False, triples=False):
    """ Delete all traces of the dataset from the Nave Storage System.

    * delete from Elastic search
    * delete from database, cascade into
        * enrichments
        * records
        * webresources
    * delete remaining triples from triple store, i.e. drop ds graph

    On deletion Narthex removes all records, mappings, and dataset information from the triple store.
    The only information left is the Dataset resource with narthex:delete 'true', see
    https://github.com/delving/narthex/blob/master/app/triplestore/Sparql.scala#L329

    """
    try:
        index_deleted = ds.delete_from_index()
        deleted, failed = ds.delete_file_stores()
        if triples:
            ds.delete_from_triple_store()
        if dataset_delete:
            ds.delete()
    except Exception as ex:
        logger.error("Unable to purge datasets: {}".format(ex))
        return False
    return True


def purge_deleted_datasets(store):
    """Find datasets which are deleted and purge all their information in Nave. """
    nr_deleted, datasets_uris = find_datasets_by_sync_or_deleted_status(store, deleted=True)
    if nr_deleted == 0:
        logger.info("No deleted datasets found.")
        return 0
    for dataset_uri in datasets_uris:
        ds = DataSet.get_dataset_from_graph(store, dataset_uri)
        delete_dataset_with_all_triples(ds, store)
        ds.delete()
    logger.info("Purged {} datasets from Nave and Narthex: {}".format(nr_deleted, datasets_uris))
    return nr_deleted


@shared_task()
def reindex_dataset(ds, acceptance=False):
    """ Reindex the dataset for elasticsearch from the edm_record cache.
    :param acceptance:
    :param ds: the DataSet
    :return: records processed
    """
    ds.processed_records = 0
    ds.save()

    def process_records():
        for edm in EDMRecord.objects.filter(dataset=ds):
            yield edm.create_es_action(
                    index=settings.SITE_NAME,
                    exclude_fields=ds.excluded_index_fields.names(),
                    context=False,
                    acceptance=acceptance
            )

    response = helpers.bulk(get_es(), actions=process_records())
    return response


@shared_task()
def save_narthex_file(ds, acceptance=False):
    ret = chain(ds.process_narthex_file(acceptance=acceptance), remove_orphaned_records(ds, acceptance=acceptance))
    return ret


@shared_task()
def remove_orphaned_records(ds, acceptance=False):
    return ds.remove_orphaned_records(acceptance=acceptance)


@shared_task
def resynchronize_dataset(ds, store=None):
    """Force synchronise Nave dataset with Narthex. """
    if not store:
        store = rdfstore.get_rdfstore()
    # clear any error
    ds.sync_error_message = ""
    ds.has_sync_error = False
    ds.save()
    response = synchronise_dataset_records.delay(
        ds=ds,
        store=store
    )
    return response


############################ Records ##############################


def find_datasets_with_records_out_of_sync(store):
    """Find all datasets that have records in the RDF store that are out of sync."""
    out_of_sync = store.ask(query="{{ ?s <http://schemas.delving.eu/narthex/terms/synced> false }}")
    if not out_of_sync:
        return 0, []
    query = """
    REDUCED ?ds
    WHERE
    { ?s2 <http://schemas.delving.eu/narthex/terms/synced> false ;
      <http://schemas.delving.eu/narthex/terms/belongsTo> ?ds ;
       a <http://xmlns.com/foaf/0.1/Document> .
     ?ds <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schemas.delving.eu/narthex/terms/Dataset> .
    }
    limit 50
    """
    res = store.select(query=query)
    ds_list = {graph['ds']['value'] for graph in res['results']['bindings']}
    return len(ds_list), ds_list


@shared_task()
def schedule_out_of_sync_datasets(acceptance=False, store=None):
    """Find all out of sync datasets and schedule synchronisation tasks for each."""
    if not store:
        store = rdfstore.get_rdfstore(acceptance)
    nr_datasets, datasets = find_datasets_with_records_out_of_sync(store)
    if nr_datasets == 0:
        return 0
    logger.info("Found {} datasets that have records that are out of sync".format(nr_datasets))
    scheduled_for_indexing = 0
    for dataset_uri in datasets:
        ds = DataSet.get_dataset_from_graph(dataset_graph_uri=dataset_uri, store=store)
        ds.records_in_sync = False
        if ds.can_be_synchronised:
            logger.info("status: {}, {}, {}".format(ds.stay_in_sync, ds.sync_in_progress, ds.has_sync_error))
            process_key = str(uuid.uuid1())
            ds.process_key = process_key
            ds.save()
            async_result = synchronise_dataset_records.apply_async(kwargs={'store': store, 'ds': ds},
                                                                   task_id=process_key)
            scheduled_for_indexing += 1
            logger.info("Scheduled {} for indexing with {} records".format(ds.spec, ds.valid))
    return scheduled_for_indexing


def get_out_of_sync_dataset_record_graph_uris(dataset_graph_uri, store, limit=50):
    """Return a list of unsynced records_graph_uris from the dataset graph. """
    if dataset_graph_uri.endswith('graph'):
        dataset_graph_uri = re.sub("/graph", "", dataset_graph_uri)
    query = """
        ?g where {{
            BIND(<{}> as ?ds)
            {{GRAPH ?g
                {{
                    ?s <http://schemas.delving.eu/narthex/terms/synced> false;
                       <http://schemas.delving.eu/narthex/terms/belongsTo> ?ds.
                       }}
                  }}
                  FILTER (!regex(str(?g), ".*skos/graph$"))
        }}
        limit {}
    """.format(dataset_graph_uri, limit)
    logger.debug("SPARQL query for getting out of sync dataset records: \n {}".format(query))
    # todo  ?ds <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schemas.delving.eu/narthex/terms/Dataset> .
    res = store.select(query=query)
    graph_list = [graph['g']['value'] for graph in res['results']['bindings']]
    return graph_list


def synchronise_record(graph_uri, ds, store, es_actions, index=settings.SITE_NAME, acceptance=False):
    # get graph
    # graph = store.get_graph_store.get(graph_uri, as_graph=True)
    graph, levels = RDFModel.get_context_graph(named_graph=graph_uri, store=store)
    # create EDM record
    edm_record = EDMRecord.graph_to_record(graph, ds)
    # create ES insert action
    index_action = edm_record.create_es_action(
        index=get_index_name(acceptance),
        record_type="Aggregated",
        store=store,
        context=False,
        exclude_fields=ds.excluded_index_fields.names()
    )
    es_actions.append(index_action)
    return edm_record, index_action


@shared_task
def synchronise_dataset_records(store, dataset_graph_uri=None, ds=None, index=settings.SITE_NAME):
    """Iterate over all records that are out of sync for a dataset and update them in the index and database. """
    if not ds and dataset_graph_uri:
        ds = DataSet.get_dataset_from_graph(dataset_graph_uri=dataset_graph_uri, store=store)
    elif ds and not dataset_graph_uri:
        dataset_graph_uri = ds.document_uri
    elif not dataset_graph_uri and not ds:
        raise ValueError("Unable to find dataset due to missing value in dataset_graph_uri and/or ds")
    logger.info("Graph uri to synchronise: {}".format(dataset_graph_uri))
    # materialize nodes
    # ore:aggregates + remove ore:isAggregatedBy
    graph_list = get_out_of_sync_dataset_record_graph_uris(dataset_graph_uri, store, 200)
    if not ds.stay_in_sync:
        logger.warn("Should not start synchronization for {} when marked as not stay in sync".format(ds.spec))
        return 0
    elif ds.has_sync_error:
        logger.warn("Can't start synchronization of {} due to previous sync error.".format(ds.spec))
        return 0
    ds.has_sync_error = False
    ds.sync_error_message = None
    ds.records_in_sync = False
    ds.processed_records = 0
    ds.save()
    records_processed = 0
    try:
        valid_records = ds.valid
        while len(graph_list) > 0:
            actions = []
            # todo use the graphs instead of the URIs
            for graph_uri in graph_list:
                synchronise_record(graph_uri, ds, store, actions, index=index)
            # index actions
            logger.info("number of actions scheduled: {}".format(len(actions)))
            response = helpers.bulk(client=get_es(), actions=actions, stats_only=True)
            records_processed += len(graph_list)
            logger.info("processed {}/{} for {}".format(records_processed, valid_records, ds.spec))
            logger.debug("ElasticSearch bulk update: {}".format(response))
            update_switch = [QueryType.remove_insert.format(
                named_graph=g,
                remove="?s <http://schemas.delving.eu/narthex/terms/synced> false",
                insert="?s <http://schemas.delving.eu/narthex/terms/synced> true"
            ) for g in graph_list]
            response = store.update(query="\n".join(update_switch))
            logger.debug("SPARQL update succeeded: {}".format(response))
            ds = DataSet.objects.get(id=ds.id)
            ds.processed_records = records_processed
            ds.save()
            graph_list = get_out_of_sync_dataset_record_graph_uris(dataset_graph_uri, store, 200)

        ds.process_key = None
        ds.records_in_sync = True
        ds.dataset_type = DataSetType.aggregated
        if not ds.oai_pmh.real > 0:
            ds.oai_pmh = OaiPmhPublished.none
        ds.save()
        logger.info("Finishing synchronising {} records from dataset: {}".format(records_processed, dataset_graph_uri))
    except Exception as e:
        logger.error("Unable to index all records for dataset {} due to {} at record {}.".format(ds.spec, e, graph_uri))
        ds.sync_error_message = "{} with error: {}".format(graph_uri, e)
        ds.has_sync_error = True
        ds.process_key = None
        ds.save()
        logger.warn("Only index {} of {} valid for dataset {}".format(records_processed, valid_records, ds.spec))
    return records_processed


def find_and_purge_deleted_records(store):
    """Delete records marked as synced from Database and Index."""
    # todo finish this
    # find the uris
    # iterate by 1000
    # es_actions to delete via hub ID
    # delete records via QuerySet


########################## SKOS Mapping ###########################


def find_out_of_sync_skos_mappings(store):
    """

    :param store:
    :return:
    """
    query = """
    SELECT *
    WHERE {
        ?s a <http://schemas.delving.eu/narthex/terms/TerminologyMapping>;
          <http://schemas.delving.eu/narthex/terms/synced> false ;
          <http://schemas.delving.eu/narthex/terms/mappingConcept> ?mc .

      ?mc a <http://schemas.delving.eu/narthex/terms/ProxyResource> ;
          <http://schemas.delving.eu/narthex/terms/belongsTo> ?ds ;
          <http://schemas.delving.eu/narthex/terms/ProxyLiteralField> ?proxy_field ;
          <http://schemas.delving.eu/narthex/terms/ProxyLiteralValue> ?proxy_value .

      ?ds <http://schemas.delving.eu/narthex/terms/skosField> ?# todo find skosfields

      ?s  <http://schemas.delving.eu/narthex/terms/mappingConcept> ?target_uri filter(?target_uri != ?mc).

      ?target_uri <http://www.w3.org/2004/02/skos/core#prefLabel> ?target_label

      }
    LIMIT 25
    """
    pass


def synchronise_out_of_sync_skos_mappings(store):
    """

    :param store:
    :return:
    """
    pass


def find_records_for_skos_mapping(store):
    """

    :param store:
    :return:
    """
    query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    SELECT ?g
    WHERE { graph ?g {
       ?s ?p <http://localhost:8000/resource/dataset/afrikamuseum/subject/potten>.

       ?s2 a foaf:Document ;
            <http://schemas.delving.eu/narthex/terms/belongsTo> ?ds ;

      }}
    LIMIT 1000
    """
    pass


def create_atomic_updates_for_skos_mappings(store):
    """

    * find the mappings
    *

    :param store:
    :return:
    """
    pass


############################ old code #############################




@shared_task()
def add_cache_urls_to_remote_resources(store=rdfstore.get_rdfstore()):
    # query = """select distinct ?s where
    #     {?s ?p ?o .
    #     FILTER (!STRSTARTS(STR(?s), "http://localhost:8000"))
    #     } limit 10
    # """
    update_query = """insert {Graph ?g  {?s <http://schemas.delving.org/nave/terms/cacheUrl> ?o2 . } }
    WHERE { Graph ?g
      { ?s ?p ?o
        Filter not exists {?s <http://schemas.delving.org/nave/terms/cacheUrl> ?o}
        FILTER ( ! strstarts(str(?s), "http://localhost:8000") ).
        BIND(URI(REPLACE(str(?s), "http://.*?/", "http://localhost:8000/resource/cache/", "i")) AS ?o2)
      }}
    """
    return store.update(update_query)
