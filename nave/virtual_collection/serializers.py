# -*- coding: utf-8 -*- 
"""This module does
"""
from rest_framework import serializers

from virtual_collection.models import VirtualCollection


class VirtualCollectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VirtualCollection
        fields = ("source_uri", "document_uri",)