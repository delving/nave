# -*- coding: utf-8 -*-
"""This module contains the tasks for storing RDFmodel
data into the graphstore.
"""
import socket
import time
from urllib.error import URLError

from celery.task import task
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from elasticsearch import helpers

from nave.lod.models import RDFModel, CacheResource
from nave.lod.utils import rdfstore
from nave.lod.utils.rdfstore import get_rdfstore


def get_es():
    from nave.search.connector import get_es_client
    return get_es_client()

logger = get_task_logger(__name__)


def get_model_label(instance):
    """Return app_label, model_name and record id from Django model record."""
    app_label = instance._meta.app_label
    model_name = instance.__class__.__name__
    record_id = instance.id
    logger.info(app_label, model_name, record_id)
    return app_label, model_name, record_id


def get_model_record(app_label, model_name, record_id):
    """Find record via parameters.idid

    Utility to find records that are put on the queue for processing.
    """
    rdf_model= apps.get_model(
        app_label=app_label,
        model_name=model_name
    )
    obj = rdf_model.objects.filter(id=record_id).first()
    if not obj:
        logger.warn(
            "Unable to find record for {}.models.{} with id {}".format(
                app_label,
                model_name,
                record_id
            )
        )
        return None
    return obj

@task()
def retrieve_and_cache_remote_lod_resource(cache_uri, store=None):
    if not store:
        store = get_rdfstore()
    cache_resource, created = CacheResource.objects.get_or_create(source_uri=cache_uri)
    return store_cache_resource.delay(cache_resource, store), created


@task()
def store_cache_resource(app_label, model_name, record_id, store=None):
    """Store cached LoD resource in the GrahpStore."""
    obj = get_model_record(app_label, model_name, record_id)
    if not store:
        store = get_rdfstore()
    graph_store = store.get_graph_store
    if not obj:
        return False
    response = obj.update_cached_resource(graph_store)
    return response


@task()
def delete_rdf_resource(app_label, model_name, record_id, store=None):
    """Delete RDF of Django model from the GraphStore."""
    obj = get_model_record(app_label, model_name, record_id)
    if not store:
        store = get_rdfstore()
    if obj and issubclass(obj.__class__, RDFModel):
        graph_store = store.get_graph_store
        response = graph_store.delete(obj.named_graph)
        logger.debug("Delete graph: {}".format(obj.named_graph))
        return response
    return False


@task()
def store_graph(app_label, model_name, record_id):
    """ Store the RDFModel subclass in the production graph store
    :param obj: a subclass of RDFModel
    :return: Boolean
    """
    obj = get_model_record(app_label, model_name, record_id)
    if obj and issubclass(obj.__class__, RDFModel):
        store = rdfstore.get_rdfstore().get_graph_store
        store.put(obj.named_graph, obj.get_graph())
        logger.debug("Stored graph data in graph: {}".format(obj.named_graph))
        return True
    return False


@task(bind=True, default_retry_delay=300, max_retries=5)
def store_graphs(triples, named_graph, store=None):
    if store is None:
        store = rdfstore.get_rdfstore()
    stored = store.get_graph_store.post(data=triples, named_graph=named_graph)
    return stored


@task(bind=True, default_retry_delay=300, max_retries=5)
def process_sparql_updates(sparql_updates, store=None):
    if store is None:
        store = rdfstore.get_rdfstore()

    def store_with_updates(update_queries):
        retries = 0
        while retries < 3:
            try:
                store.update("\n".join(sparql_updates))
                update_queries.clear()
                return True
            except (URLError, socket.timeout) as e:
                retries += 1
                logger.error("sparql update timeout with retries {} and error {}".format(retries, e))
                time.sleep(3)
        if retries > 2:
            #   todo: log the items in the db as not synced
            pass
        return False

    updates = []
    for i, update in enumerate(sparql_updates):
        updates.append(update)
        if i % 25 == 0:
            store_with_updates(updates)
            updates[:] = []
    store_with_updates(updates)


@task()
def remove_rdf_from_index(
    app_label, model_name, record_id, index=settings.INDEX_NAME, store=None
    ):
    """Remove RDF for Django Record from the GraphStore."""
    obj = get_model_record(app_label, model_name, record_id)
    if obj and issubclass(obj.__class__, RDFModel):
        nr, errors = helpers.bulk(
            get_es(),
            [obj.create_es_action(action='delete', index=index, store=store)],
            raise_on_error=False
        )
        if nr > 0 and not errors:
            logger.info("Removed records: {}".format(nr))
            return True
        elif errors:
            logger.warn("Something went wrong with bulk index: {}".format(errors))
            return False
    return False


@task()
def update_rdf_in_index(app_label, model_name, record_id,
                        index=settings.INDEX_NAME, store=None):
    obj = get_model_record(app_label, model_name, record_id)
    if obj and issubclass(obj.__class__, RDFModel):
        nr, errors = helpers.bulk(get_es(), [obj.create_es_action(index=index, store=store, context=False)])
        if nr > 0 and not errors:
            logger.info("Indexed records: {}".format(nr))
            return True
        elif errors:
            logger.warn("Something went wrong with bulk index: {}".format(errors))
            return False
    return False
