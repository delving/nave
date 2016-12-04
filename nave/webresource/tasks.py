# coding=utf-8
from celery import shared_task
from celery.task import task
from celery.utils.log import get_task_logger

from lod.utils import rdfstore

logger = get_task_logger(__name__)


@shared_task()
def create_webresource_dirs(endpoint=None):
    if endpoint is None:
        endpoint = rdfstore.get_sparql_base_url()

    from void.views import DataSetStatistics
    stats = DataSetStatistics(endpoint)
    specs = stats.get_spec_list(include_deleted=False)
    created_dirs = 0
    logger.info("Start syncing WebResource directories")
    for spec in specs.keys():
        logger.info(spec)
        from webresource.webresource import WebResource
        webresource = WebResource(spec=spec)
        created = webresource.create_dataset_webresource_dirs()
        if created:
            created_dirs += 1

    logger.info("Finished syncing WebResource directories. Created {}".format(created_dirs))


@task()
def create_deepzoom(uri, spec):
    """Celery function for creating deepzoom images."""
    from webresource.webresource import WebResource
    wr = WebResource(uri=uri, spec=spec)
    if not wr.exists_deepzoom:
        return wr.create_deepzoom()