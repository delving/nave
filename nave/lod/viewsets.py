# -*- coding: utf-8 -*- 
"""This module does
"""

from rest_framework import viewsets
from nave.lod.models import CacheResource
from nave.lod.serializers import CacheResourceSerializer


class CacheResourceViewSet(viewsets.ModelViewSet):
    queryset = CacheResource.objects.all()
    serializer_class = CacheResourceSerializer
