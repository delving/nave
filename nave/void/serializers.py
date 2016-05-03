# coding=utf-8
from rest_framework import serializers

from .models import UserGeneratedContent


class UserGeneratedContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserGeneratedContent