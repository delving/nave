# -*- coding: utf-8 -*-
"""
All the Django Rest Framework (http://www.django-rest-framework.org/tutorial/quickstart)
serializers
"""

from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .search import FacetCountLink, FacetLink, NaveFacets, NaveQueryResponse


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        lookup_field = 'username'
        fields = ('username', 'email', 'is_staff', 'first_name', 'last_name')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class FacetCountLinkSerializer(serializers.Serializer):
    url = serializers.CharField(source='link')
    isSelected = serializers.BooleanField(source='is_selected')
    value = serializers.CharField()
    count = serializers.IntegerField()
    displayString = serializers.CharField(source="display_string")

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"
        model = FacetCountLink


class FacetLinkSerializer(serializers.Serializer):
    name = serializers.CharField()
    isSelected = serializers.BooleanField(source='is_facet_selected')
    i18n = serializers.CharField()
    total = serializers.IntegerField()
    missingDocs = serializers.IntegerField(source="missing_count")
    otherDocs = serializers.IntegerField(source="other_count")
    links = FacetCountLinkSerializer(many=True)

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"
        model = FacetLink


class NaveFacetSerializer(serializers.Serializer):
    facets = FacetLinkSerializer(source='facet_query_links', many=True)

    class Meta:
        model = NaveFacets


class BreadCrumbSerializer(serializers.Serializer):
    href = serializers.CharField()
    display = serializers.CharField()
    field = serializers.CharField()
    localised_field = serializers.CharField(allow_blank=True)
    value = serializers.CharField()
    is_last = serializers.BooleanField()


class UserQuerySerializer(serializers.Serializer):
    numfound = serializers.IntegerField(source='num_found')
    terms = serializers.CharField()
    breadCrumbs = BreadCrumbSerializer(source='breadcrumbs', many=True)


class PageLinkSerializer(serializers.Serializer):
    start = serializers.IntegerField()
    isLinked = serializers.BooleanField(source="is_linked")
    pageNumber = serializers.IntegerField(source="page_number")


class QueryPaginationSerializer(serializers.Serializer):
    start = serializers.IntegerField()
    rows = serializers.IntegerField()
    numFound = serializers.IntegerField(source="num_found")
    hasNext = serializers.BooleanField(source="has_next")
    nextPage = serializers.IntegerField(source="next_page_start")
    currentPage = serializers.IntegerField(source="current_page")
    nextPageNumber = serializers.IntegerField(source="next_page_number")
    hasPrevious = serializers.BooleanField(source="has_previous")
    previousPage = serializers.IntegerField(source="previous_page_start")
    previousPageNumber = serializers.IntegerField(source="previous_page_number")
    firstPage = serializers.IntegerField(source="first_page")
    lastPage = serializers.IntegerField(source="last_page")
    links = PageLinkSerializer(many=True)


class NaveESFieldSerializer(serializers.BaseSerializer):

    def to_representation(self, instance):
        return instance


class NaveESItemSerializer(serializers.Serializer):
    doc_id = serializers.CharField()
    doc_type = serializers.CharField()
    # TODO maybe add custom field serializer later
    fields = NaveESFieldSerializer()


class NaveESItemWrapperSerializer(serializers.Serializer):
    item = NaveESItemSerializer()


class NaveESItemMLTWrapperSerializer(serializers.Serializer):
    # todo finish this with new query
    item = NaveESItemSerializer()
    # relatedItems = NaveESItemWrapperSerializer(source="related_items", many=True)


class LayoutSerializer(serializers.Serializer):
    name = serializers.CharField()
    i18n = serializers.CharField()


class LayoutWrapperSerializer(serializers.Serializer):
    layout = LayoutSerializer(many=True)


class NaveQueryResponseSerializer(serializers.Serializer):
    query = UserQuerySerializer(source='user_query')
    pagination = QueryPaginationSerializer()
    # layout = LayoutWrapperSerializer(many=False)
    items = NaveESItemWrapperSerializer(many=True)
    facets = FacetLinkSerializer(source='facet_query_links', many=True)

    class Meta:
        model = NaveQueryResponse


class NaveQueryResponseWrapperSerializer(serializers.Serializer):
    result = NaveQueryResponseSerializer(source='response', many=False)


class NaveItemResponseSerializer(serializers.Serializer):
    result = NaveESItemWrapperSerializer(many=False)
