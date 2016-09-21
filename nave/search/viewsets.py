# -*- coding: utf-8 -*- 
"""Viewsets for the Django Rest Framework

For more information, see http://www.django-rest-framework.org/api-guide/viewsets/

"""
from django.contrib.auth.models import User, Group
from oauth2_provider.ext.rest_framework import TokenHasScope
from oauth2_provider.models import AccessToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from nave.search.serializers import UserSerializer, GroupSerializer


class OauthTokenViewSet(ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    def list(self, request, *args, **kwargs):
        if not request.auth:
            return Response({})
        token = AccessToken.objects.get(token=request.auth)
        if not token:
            return Response({})
        user = token.user
        serializer = self.get_serializer(user, many=False)
        return Response(serializer.data)

    queryset = User.objects.all()
    serializer_class = UserSerializer
    required_scopes = ['read']
    permission_classes = (IsAuthenticated, TokenHasScope)


class UserViewSet(ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class GroupViewSet(ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)

# class DataSetViewSet(viewsets.ModelViewSet):
#     queryset = DataSet.objects.all()
#     serializer_class = DataSetSerializer
#
#
# class SchemaVersionViewSet(viewsets.ModelViewSet):
#     queryset = SchemaVersion.objects.all()
#     serializer_class = SchemaVersionSerializer
#
#
# class SchemaPrefixViewSet(viewsets.ModelViewSet):
#     queryset = SchemaPrefix.objects.all()
#     serializer_class = SchemaPrefixSerializer
