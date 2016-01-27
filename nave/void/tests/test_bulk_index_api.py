import os

from django.conf import settings
from django.test import override_settings
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory, APIClient

from lod.utils import rdfstore
from void.processors import BulkApiProcessor

user = User.objects.get_or_create(username='test_user')
factory = APIRequestFactory()
client = APIClient()
client.force_authenticate(user=user)


@override_settings(
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_ALWAYS_EAGER=True,
    BROKER_BACKEND='memory')
@pytest.mark.django_db
def test__processors__bulk_call():
    path = os.path.join(settings.DJANGO_ROOT, "void", "tests", "resources", "bulk_api_sample.txt")
    with open(path, 'r') as f:
        processor = BulkApiProcessor(f, store=rdfstore._rdfstore_test)
        assert processor
        processor.process()
        stats = processor._processing_statistics()
        assert stats
