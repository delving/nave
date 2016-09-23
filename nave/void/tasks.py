# -*- coding: utf-8 -*-

import socket
from urllib.error import URLError

from celery import shared_task, task, chain
from celery.utils.log import get_task_logger
from django.conf import settings
from nave.void.processors import BulkApiProcessor

logger = get_task_logger(__name__)
########################### Bulk API ##############################


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

