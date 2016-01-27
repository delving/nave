from django.contrib import admin
import reversion
from virtual_collection.models import VirtualCollection


class VirtualCollectionAdmin(reversion.VersionAdmin):
    list_filter = ['user', 'group']
    filter_horizontal = ('group',)
    list_display = ('title', 'user')


admin.site.register(VirtualCollection, VirtualCollectionAdmin)

