# -*- coding: utf-8 -*-
"""This module does
"""
from rest_framework import serializers

from .models import VirtualWebsite


class VirtualCollectionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VirtualWebsite
        fields = ("slug", "title",)

class VirtualWebsitePageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VirtualWebsitePage
        fields = ("slug", "title",)
