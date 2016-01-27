# -*- coding: utf-8 -*- 
"""This module does
"""

from rest_framework import viewsets
from lod.models import CacheResource
from lod.serializers import CacheResourceSerializer


class CacheResourceViewSet(viewsets.ModelViewSet):
    queryset = CacheResource.objects.all()
    serializer_class = CacheResourceSerializer
