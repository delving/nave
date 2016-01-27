from django.contrib import admin
from .models import DiwInstance, DiwFacet, DiwResultField, DiwDetailField

"""
TODO: field names should be retrieved dynamically from a schema or model and selected by the user from a dropwdown
"""

class FacetInline(admin.TabularInline):
    model = DiwFacet
    fields = ['name', 'label', 'position']
    extra = 0
    max_num = 6


class ResultFieldInline(admin.TabularInline):
    model = DiwResultField
    fields = ['name', 'label', 'position']
    extra = 0
    max_num = 3


class ItemFieldInline(admin.TabularInline):
    model = DiwDetailField
    fields = ['name', 'label', 'position']
    extra = 0
    max_num = 24


class DiwInstanceAdmin(admin.ModelAdmin):
    fields = ['name', 'collection_spec']
    inlines = (FacetInline, ResultFieldInline, ItemFieldInline,)


admin.site.register(DiwInstance, DiwInstanceAdmin)