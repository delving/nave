import logging

from django import template
from django.conf import settings

from nave.search.connector import get_es_client
from elasticsearch_dsl import Search, Q
from nave.void.models import DataSet

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
        s = Search(using=get_es_client(), index=settings.INDEX_NAME)

        #object_count = get_es_client().count(index=settings.INDEX_NAME, doc_type="void_edmrecord")['count']
        #s = s.query('match', legacy__delving_recordType='mdr').extra(track_total_hits=True)[0]
        s = s.extra(track_total_hits=True)[0]
        hits = s.execute()
        return {'datasets': dataset_count, 'objects': hits.hits.total.value}
    except:
        return {'datasets': 0, 'objects': 0}
