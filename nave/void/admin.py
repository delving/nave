import logging

import reversion
from django.conf import settings
from django.contrib import admin
from django.utils import importlib
from django_object_actions import takes_instance_or_queryset

from nave.lod.utils import rdfstore
from nave.void import tasks
from nave.void.models import DataSet, EDMRecord, ProxyResourceField, ProxyMapping, ProxyResource

logger = logging.getLogger(__name__)


@takes_instance_or_queryset
def reindex_dataset(self, request, queryset):
    records_processed = 0
    ds_processed = 0
    for ds in queryset:
        tasks.reindex_dataset.delay(ds)
        ds_processed += 1
        records_processed += ds.valid
    self.message_user(request, "{} dataset(s) processed with {} records".format(ds_processed, records_processed))


reindex_dataset.short_description = "Reindex dataset in production"


@takes_instance_or_queryset
def disable_dataset_in_index(self, request, queryset):
    records_processed = 0
    ds_processed = 0
    for ds in queryset:
        tasks.disable_dataset_in_index.delay(ds)
        ds_processed += 1
        records_processed += ds.valid
    self.message_user(request, "{} dataset(s) disabled with {} records".format(ds_processed, records_processed))


disable_dataset_in_index.short_description = "Disable dataset in production index"


@takes_instance_or_queryset
def reindex_dataset_acceptance(self, request, queryset):
    records_processed = 0
    ds_processed = 0
    for ds in queryset:
        tasks.reindex_dataset.delay(ds, acceptance=True)
        ds_processed += 1
        records_processed += ds.valid
    self.message_user(request, "{} dataset(s) processed with {} records".format(ds_processed, records_processed))


reindex_dataset_acceptance.short_description = "Reindex dataset in acceptance"


@takes_instance_or_queryset
def save_narthex_file_acceptance(self, request, queryset):
    records_processed = 0
    ds_processed = 0
    for ds in queryset:
        tasks.save_narthex_file.delay(ds, acceptance=True)
        ds_processed += 1
        records_processed += ds.valid
    self.message_user(request, "{} dataset(s) saved with {} records".format(ds_processed, records_processed))


save_narthex_file_acceptance.short_description = "Save narthex processed dataset in acceptance"


@takes_instance_or_queryset
def save_narthex_file_production(self, request, queryset):
    records_processed = 0
    ds_processed = 0
    for ds in queryset:
        tasks.save_narthex_file.delay(ds, acceptance=False)
        ds_processed += 1
        records_processed += ds.valid
    self.message_user(request, "{} dataset(s) saved with {} records".format(ds_processed, records_processed))


save_narthex_file_production.short_description = "Save narthex processed dataset in production"

@takes_instance_or_queryset
def stop_celery_task_by_id(self, request, queryset):
    """Stop a running Dataset synchronisation task in celery."""
    # find app in settings module
    celery_app = importlib.import_module("nave.projects.{}.celeryapp".format(settings.SITE_NAME))
    app = celery_app.app
    for ds in queryset:
        if ds.process_key:
            app.control.revoke(ds.process_key, terminate=True)
        ds.process_key = None
        ds.save()
    self.message_user(request, "Stopped synchronisation for selected datasets.")


stop_celery_task_by_id.short_description = "Stop DataSet synchronisation task"


@takes_instance_or_queryset
def reset_dataset_content_hashes(self, request, queryset):
    for ds in queryset:
        EDMRecord.objects.filter(dataset=ds).update(source_hash=None)

reset_dataset_content_hashes.short_description = "Reset record content hashes for production"


@takes_instance_or_queryset
def reset_dataset_content_hashes_acceptance(self, request, queryset):
    for ds in queryset:
        EDMRecord.objects.filter(dataset=ds).update(acceptance_hash=None)

reset_dataset_content_hashes_acceptance.short_description = "Reset record content hashes for acceptance"


class ProxyResourceFieldInline(admin.TabularInline):
    model = ProxyResourceField
    fields = ["search_label", "property_uri"]


class ProxyResourceInline(admin.TabularInline):
    model = ProxyResource


class DataSetAdmin(reversion.admin.VersionAdmin):
    inlines = [ProxyResourceFieldInline]

    actions = [disable_dataset_in_index, reindex_dataset, reindex_dataset_acceptance, reset_dataset_content_hashes,
               reset_dataset_content_hashes_acceptance, save_narthex_file_production, save_narthex_file_acceptance]
    search_fields = ['name', 'spec', 'data_owner']

    list_display = ['name', 'spec', 'data_owner', 'valid', 'invalid', 'total_records']
    list_filter = ('data_owner', 'published', 'created', 'modified')

# admin.site.register(DataSet, DataSetAdmin)


class ProxyResourceFieldAdmin(reversion.admin.VersionAdmin):
    # inlines = [ProxyResourceInline]

    list_display = ['property_uri', 'search_label', 'spec']
    list_filter = ('dataset__spec', 'modified', 'created')

    def spec(self, obj):
        return obj.dataset.spec
    spec.short_description = 'Dataset Spec'


admin.site.register(ProxyResourceField, ProxyResourceFieldAdmin)


class ProxyResourceAdmin(reversion.admin.VersionAdmin):
    # inlines = [ProxyResourceInline]

    list_display = ['proxy_uri', 'spec', 'search_label']
    list_filter = (
        'dataset__spec',
        'proxy_field__search_label',
        'modified',
        'created'
    )

    def search_label(self, obj):
        return obj.proxy_field.search_label
    search_label.short_description = 'Proxy Field'

    def spec(self, obj):
        return obj.dataset.spec
    spec.short_description = 'Dataset Spec'


admin.site.register(ProxyResource, ProxyResourceAdmin)


class ProxyMappingAdmin(reversion.admin.VersionAdmin):
    # inlines = [ProxyResourceInline]

    list_display = ['skos_concept_uri', 'proxy_resource_uri', 'spec']
    list_filter = (
        'proxy_resource__proxy_field__dataset__spec',
        'proxy_resource__proxy_field__search_label',
        'modified',
        'created'
    )

    def spec(self, obj):
        return obj.proxy_resource.proxy_field.dataset.spec
    spec.short_description = 'Dataset Spec'


admin.site.register(ProxyMapping, ProxyMappingAdmin)


class EDMRecordAdmin(reversion.admin.VersionAdmin):
    search_fields = ('hub_id', 'slug', 'document_uri', 'source_rdf', 'acceptance_rdf')
    list_filter = ['dataset__spec', 'dataset__data_owner', 'modified']
    show_full_result_count = False

# admin.site.register(EDMRecord, EDMRecordAdmin)
