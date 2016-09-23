<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""This module does contains the synchronisation tasks that keep the
metadata records stored in RDF store by Narthex in sync with the the Nave
database and search index.
||||||| parent of b068025... Boyscout: Removing all spurious <U+2028> linebreaks
# -*- coding: utf-8 -*- 
=======
# -*- coding: utf-8 -*-
>>>>>>> b068025... Boyscout: Removing all spurious <U+2028> linebreaks

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

from nave.void.processors import BulkApiProcessor

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
        logger.error("Got url error for {}, but will retry again".format(ue))
        self.retry()
    except socket.timeout as to:
        logger.error("Got socket timeout for {}, but will retry again".format(to))
        self.retry()
    except socket.error as err:
        logger.error("Got socket error for {}, but will retry again".format(err))
        self.retry()

