# -*- coding: utf-8 -*- 
from django.conf import settings
from django.contrib import admin
from django.db.models import Q
import reversion

from .models import RDFPrefix, SPARQLQuery, SPARQLUpdateQuery, CacheResource


class GroupOwnedAdmin(admin.ModelAdmin):
    """
    Admin class for models that subclass the abstract ``Owned``
    model. Handles limiting the change list to objects owned by the
    logged in user, as well as setting the owner of newly created
    objects to the logged in user.

    Remember that this will include the ``user`` field in the required
    fields for the admin change form which may not be desirable. The
    best approach to solve this is to define a ``fieldsets`` attribute
    that excludes the ``user`` field or simple add ``user`` to your
    admin excludes: ``exclude = ('user',)``
    """

    def save_form(self, request, form, change):
        """
        Set the object's owner as the logged in user.
        """
        obj = form.save(commit=False)
        if obj.user_id is None:
            obj.user = request.user
        return super(GroupOwnedAdmin, self).save_form(request, form, change)

    def queryset(self, request):
        """
        Filter the change list by currently logged in user if not a
        superuser. We also skip filtering if the model for this admin
        class has been added to the sequence in the setting
        ``OWNABLE_MODELS_ALL_EDITABLE``, which contains models in the
        format ``app_label.object_name``, and allows models subclassing
        ``Owned`` to be excluded from filtering, eg: ownership should
        not imply permission to edit.
        """
        opts = self.model._meta
        model_name = ("%s.%s" % (opts.app_label, opts.object_name)).lower()
        models_all_editable = settings.OWNABLE_MODELS_ALL_EDITABLE
        models_all_editable = [m.lower() for m in models_all_editable]
        qs = super(GroupOwnedAdmin, self).queryset(request)
        if request.user.is_superuser or model_name in models_all_editable:
            return qs
        return qs.filter(Q(groups__in=request.user.groups.values_list('id', flat=True)) | Q(user__id=request.user.id))


class SPARQLQueryAdmin(reversion.VersionAdmin):
    list_filter = ['prefixes', 'modified']
    filter_horizontal = ('prefixes',)
    fields = ['title', 'prefixes', 'query', 'description']

admin.site.register(SPARQLQuery, SPARQLQueryAdmin)


class RDFPrefixAdmin(reversion.VersionAdmin):
    pass

admin.site.register(RDFPrefix, RDFPrefixAdmin)


class CacheResourceAdmin(reversion.VersionAdmin):
    pass

admin.site.register(CacheResource, CacheResourceAdmin)


class SPARQLUpdateQueryAdmin(reversion.VersionAdmin):
    list_filter = ['prefixes', 'modified']
    filter_horizontal = ('prefixes',)
    fields = ['title', 'prefixes', 'query', 'description']

admin.site.register(SPARQLUpdateQuery, SPARQLUpdateQueryAdmin)