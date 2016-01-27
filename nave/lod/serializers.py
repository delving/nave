# -*- coding: utf-8 -*- 
"""This module does

"""
from rest_framework import serializers

from lod.models import CacheResource


class CacheResourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CacheResource
        fields = ("source_uri", "document_uri")
