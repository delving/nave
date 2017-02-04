import os

from django.test import override_settings

from nave.lod.utils import rdfstore
from nave.void.processors import BulkApiProcessor


def test__processors__single_call():
    pass


@override_settings(
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_ALWAYS_EAGER=True,
    BROKER_BACKEND='memory')
def test__processors__bulk_call():
    with open(os.path.join(os.path.dirname(__file__), 'resources/bulk_api_sample.txt'), 'r') as f:
        processor = BulkApiProcessor(f, store=rdfstore._rdfstore_test)
        assert processor
