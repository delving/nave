import logging

from django import template
from django.conf import settings

from void import get_es
from void.models import DataSet

register = template.Library()

logger = logging.getLogger(__name__)


@register.assignment_tag
def data_counts():
    """
    return the total number of 'active' datasets
    :return: dataset_count
    """

    try:
        dataset_count = DataSet.objects.count()
        object_count = get_es().count(index=settings.SITE_NAME, doc_type="void_edmrecord")['count']

        return {'datasets': dataset_count, 'objects': object_count}
    except:
        return {'datasets': 0, 'objects': 0}
