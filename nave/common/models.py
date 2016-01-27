# -*- coding: utf-8 -*- 
"""This module does


"""
from django.db import models
from django.db.models import TextField
from django.utils.translation import ugettext_lazy as _


class RichText(models.Model):
    """
    Provides a Rich Text field for managing general content and making
    it searchable.
    """

    content = TextField(_("Content"), blank=True, null=True)

    search_fields = ("content",)

    class Meta:
        abstract = True
