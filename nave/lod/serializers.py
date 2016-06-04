# -*- coding: utf-8 -*- 
from rest_framework import serializers

from .models import CacheResource, UserGeneratedContent


class CacheResourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CacheResource
        fields = ("source_uri", "document_uri")


class UserGeneratedContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserGeneratedContent
        exclude = ('groups', 'user', 'html_summary')
