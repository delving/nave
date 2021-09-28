from django.contrib import admin
from django.forms import ModelForm

import reversion
from suit_ckeditor.widgets import CKEditorWidget

from .models import VirtualCollection, VirtualCollectionFacet, VirtualCollectionOrQuery


class VirtualCollectionForm(ModelForm):
    class Meta:
        widgets = {
            'body': CKEditorWidget(editor_options={'startupFocus': True})
        }


class FacetInline(admin.TabularInline):
    model = VirtualCollectionFacet
    fields = ['name', 'label', 'position']
    extra = 0
    max_num = 8

class OrQueryInline(admin.TabularInline):
    model = VirtualCollectionOrQuery
    fields = ['query', 'position']
    extra = 0
    max_num = 8

class VirtualCollectionAdmin(reversion.admin.VersionAdmin):
    list_filter = ['user', 'groups']
    filter_horizontal = ('groups',)
    list_display = ('title', 'user')
    form = VirtualCollectionForm
    inlines = (OrQueryInline, FacetInline,)
    fieldsets = [
        ('Description', {'classes': ('full-width',), 'fields': ('title',)}),
        ('Query', {'classes': ('full-width',), 'fields': ('query',)}),
        ('Body', {'classes': ('full-width',), 'fields': ('body',)}),
        ('Meta', {'fields': ('groups', 'user', 'oai_pmh', 'published', 'owner', 'creator')})
    ]


admin.site.register(VirtualCollection, VirtualCollectionAdmin)

