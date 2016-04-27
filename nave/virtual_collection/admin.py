from django.contrib import admin
from django.forms import ModelForm

import reversion
from suit_ckeditor.widgets import CKEditorWidget

from .models import VirtualCollection


class VirtualCollectionForm(ModelForm):
    class Meta:
        widgets = {
            'body': CKEditorWidget(editor_options={'startupFocus': True})
        }


class VirtualCollectionAdmin(reversion.admin.VersionAdmin):
    list_filter = ['user', 'groups']
    filter_horizontal = ('groups',)
    list_display = ('title', 'user')
    form = VirtualCollectionForm
    fieldsets = [
        ('Description', {'classes': ('full-width',), 'fields': ('title', 'query')}),
        ('Body', {'classes': ('full-width',), 'fields': ('body',)}),
        ('Meta', {'fields': ('groups', 'user', 'oai_pmh', 'published', 'owner', 'creator')})
    ]


admin.site.register(VirtualCollection, VirtualCollectionAdmin)

