# -*- coding: utf-8 -*- 
from rest_framework import serializers

from .models import CacheResource, UserGeneratedContent


class CacheResourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CacheResource
        fields = ("source_uri", "document_uri")


class UserGeneratedContentSerializer(serializers.ModelSerializer):

    def create(self, data):
        # Will only be done if a new object is being created
        data['user'] = self.context.get('request')._user
        return super().create(data)

    class Meta:
        model = UserGeneratedContent
        exclude = ('groups', 'html_summary')
