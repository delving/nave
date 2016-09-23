# -*- coding: utf-8 -*-
"""This module handles all the celery tasks for the search app

"""
import os
import time
import uuid

from celery import shared_task
from celery.task import task
from celery.utils.log import get_task_logger
from django.conf import settings
from elasticsearch.helpers import scan

from search import es_client as es
from search.search import NaveESItemList

logger = get_task_logger(__name__)


@shared_task
def clean_up_old_downloads():
    # clean up downloads that are older than 1 day
    # scan folder
    # find files older than 1 day
    # remove them
    # return number of zips removed
    pass


@task()
def download_all_search_results(query_dict, index_name, converter,
                                doc_types, response_format='json'):
    """
    This function creates a downloadable zip-file for a ElasticSearch
    result set that will be emailed to the user.


    # TODO update the parameters for the function
    :type query_dict: object
    :return: path to object returned
    """
    # response_format = request.GET.get('format', 'json')
    # if not request.user.is_authenticated():
    #     logger.warn("Only logged in users can create a download request.")
    #     return 0
    # else:
    #     user = request.user
    # with open(os.path.join(settings.ZIPPED_SEARCH_RESULTS_DOWNLOAD_FOLDER,
    #                        "{}_{}.{}".format(user.username, uuid.uuid1(), response_format))) as f:
    #     pass

    # ensure download dir exist

    downloader = scan(
        client=es,
        query=query_dict,
        index=index_name,
        doc_type=doc_types
    )
    download_file = os.path.join(
        settings.ZIPPED_SEARCH_RESULTS_DOWNLOAD_FOLDER,
        "{}_{}.{}".format(uuid.uuid1(), converter, response_format))
    with open(download_file, 'w') as f:
        f.write('[\n')
        for results in downloader:
            items = NaveESItemList(
                results=results,
                converter=converter
            ).items
            f.write(items)
            # todo serializers for other formats than JSON
        f.write('\n]\n')


    # create elasticsearch.helper.scan object
    # for each response convert to Nave Response Item and apply converter
    # write the records to file
    # when done create download link
    # compose email to user with
    # - link
    # - query
    # - records saved
    # - format
    # - request time

    logger.info("started")
    time.sleep(3)
    logger.info("ended")
    logger.info(query_dict)
    link = "link"
    records_returned = 10
    return link, query_dict, records_returned, format
