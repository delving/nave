# -*- coding: utf-8 -*-
"""
This class holds the models for the 'void' app.

The core classes that need to be stored are:

* Datasets: any grouping of RDF records is a dataset
    * dataset proxies:
        * LinkedSet:
        * VirtualDataSet:
* EDM records: any record that contains
"""
import logging
import os
import re
import shutil
import time
from functools import partial

from dateutil import parser
from dj.choices import Choices, Choice
from dj.choices.fields import ChoiceField
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import AutoSlugField
from django_extensions.db.models import TimeStampedModel, TitleDescriptionModel
from elasticsearch import helpers
from rdflib import URIRef, Graph, Literal, ConjunctiveGraph
from rdflib.namespace import RDF, SKOS

from lod import namespace_manager
from lod.models import RDFModel
from lod.utils import rdfstore
from lod.utils.resolver import RDFPredicate, RDFRecord
from lod.utils.rdfstore import QueryType, RDFStore

logger = logging.getLogger(__name__)

fmt = '%Y-%m-%d %H:%M:%S%z'  # '%Y-%m-%d %H:%M:%S %Z%z'

def get_es():
    from search import get_es_client
    return get_es_client()


def get_user_model_name():
    """
    Returns the app_label.object_name string for the user model.
    """
    return getattr(settings, "AUTH_USER_MODEL", "auth.User")


user_model_name = get_user_model_name()


class GroupOwned(models.Model):
    """
    Abstract model that provides ownership of an object for a User and optional Groups.
    """
    user = models.ForeignKey(
            user_model_name,
            verbose_name=_("Author"),
            help_text=_("The first creator of the object"),
            blank=True,
            null=True,
            related_name="%(class)ss"
    )
    groups = models.ManyToManyField(
            Group,
            verbose_name=_("Group"),
            help_text=_("The groups that have access to this metadata record"),
            blank=True,
    )

    class Meta(object):
        abstract = True

    def has_group_access(self, request):
        user_groups = request.user.groups.values_list('id', flat=True)
        object_groups = self.groups.values_list('id', flat=True)
        return set(object_groups).intersection(set(user_groups))

    def is_editable(self, request):
        """
        Restrict in-line editing to the object's owner,  and superusers.
        """
        return request.user.is_superuser or request.user.id == self.user_id or self.has_group_access(request)


class OaiPmhPublished(Choices):
    none = Choice(_("None"))
    public = Choice(_("Public"))
    protected = Choice(_("Protected"))


class DataSetType(Choices):
    aggregated = Choice(_("Aggregated"))
    primary = Choice(_("Primary source"))
    cached = Choice(_("Cached"))
    skos = Choice(_("SKOS"))
    placeholder = Choice(_("Placeholder"))


class ProxyResourceField(TimeStampedModel):
    """
    This class contains the RDF properties of which all the literal values need to be converted into RDF
    ProxyResources.

    The goal of the ProxyResource is to function as the anker point for mappings from Thesauri or other enrichments.
    """

    property_uri = models.URLField()
    search_label = models.CharField(max_length=56)
    dataset_uri = models.URLField()
    dataset = models.ForeignKey('DataSet', blank=True, null=True)

    class Meta:
        unique_together = ("property_uri", "dataset_uri")
        verbose_name = _("Proxy Resource Field")
        verbose_name_plural = _("Proxy Resource Field")

    def __str__(self):
        return self.property_uri

    @staticmethod
    def get_proxy_field_by_uri(uri, ds):
        if ProxyResourceField.objects.filter(property_uri=uri, dataset=ds).exists():
            return ProxyResourceField.objects.get(property_uri=uri, dataset=ds)
        field = ProxyResourceField(
                property_uri=uri,
                dataset_uri=ds.document_uri,
                dataset=ds
        )
        field.save()
        return field

    @staticmethod
    def get_proxy_field(search_label, ds):
        if ProxyResourceField.objects.filter(search_label=search_label, dataset=ds).exists():
            return ProxyResourceField.objects.get(search_label=search_label, dataset=ds)
        if '_' not in search_label:
            raise ValueError("search_label {} should contain an underscore '_'.".format(search_label))
        prefix, label = search_label.split('_', maxsplit=1)
        uri_prefix = settings.RDF_SUPPORTED_PREFIXES.get(prefix)
        if not uri_prefix:
            raise ValueError("unknown prefix: {}".format(prefix))
        field = ProxyResourceField(
                property_uri="{}/{}".format(uri_prefix, label),
                search_label=search_label,
                dataset_uri=ds.document_uri,
                dataset=ds
        )
        field.save()
        return field

    def save(self, *args, **kwargs):
        if not self.search_label:
            self.search_label = RDFPredicate(self.property_uri).search_label
        if not self.dataset:
            ds = DataSet.get_dataset(document_uri=self.dataset_uri)
            self.dataset = ds
        super(ProxyResourceField, self).save(*args, **kwargs)


class ProxyMapping(TimeStampedModel):
    user_uri = models.URLField()
    proxy_resource_uri = models.URLField()
    skos_concept_uri = models.URLField()

    user = models.ForeignKey(User, blank=True, null=True)
    proxy_resource = models.ForeignKey('ProxyResource', blank=True, null=True)

    mapping_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    mapping_object = GenericForeignKey('mapping_type', 'object_id')

    class Meta(object):
        verbose_name = _("Proxy Mapping")
        verbose_name_plural = _("Proxy Mappings")

    def __str__(self):
        return "{} => {}".format(self.proxy_resource_uri, self.skos_concept_uri)

    def save(self, *args, **kwargs):
        self.proxy_resource = ProxyResource.get_proxy_resource_from_uri(self.proxy_resource_uri)
        # todo remove later with real mapping reference
        self.mapping_object = self.proxy_resource
        super(ProxyMapping, self).save(*args, **kwargs)

    @staticmethod
    def get_skos_from_uri(skos_uri, store=None):
        if store is None:
            store = rdfstore.get_rdfstore()
        response = EDMRecord.get_skos_broader_context_graph(store, skos_uri)
        g = Graph()
        g.namespace_manager = namespace_manager
        for entry in response['results']['bindings']:
            if all([key in ['broader', 'prefLabel', 's'] for key in entry.keys()]):
                triple = (URIRef(entry['broader']['value']), SKOS.prefLabel,
                          Literal(entry['prefLabel']['value'], lang=entry['prefLabel'].get('xml:lang')))
                g.add(triple)
                g.add((URIRef(entry['s']['value']), SKOS.broader, URIRef(entry['broader']['value'])))
            elif all([key in ['s', 'p', 'o'] for key in entry.keys()]):
                subject = URIRef(entry['s']['value'])
                predicate = URIRef(entry['p']['value'])
                obj_value = entry['o']
                if obj_value['type'] == 'literal':
                    obj = Literal(obj_value['value'], lang=obj_value.get('xml:lang'))
                else:
                    obj = URIRef(obj_value['value'])
                g.add((subject, predicate, obj))
        return g

    def get_mapping_target_graph(self, store=None):
        if not issubclass(self.mapping_object.__class__, RDFModel):
            graph = self.get_skos_from_uri(skos_uri=self.skos_concept_uri, store=store)
        else:
            graph = self.mapping_object.get_graph()
        return graph


class ProxyResource(TimeStampedModel):
    proxy_uri = models.URLField(unique=True, blank=False, null=False)
    proxy_field = models.ForeignKey(ProxyResourceField)
    dataset = models.ForeignKey('DataSet')
    frequency = models.IntegerField(default=0)
    label = models.TextField(blank=False, null=False)
    language = models.CharField(max_length=26, blank=True, null=True)

    # mapping through reverse mapping

    class Meta(object):
        verbose_name = _("Proxy Resource")
        verbose_name_plural = _("Proxy Resources")

    def has_mapping(self):
        return self.proxymapping_set.exists()

    def get_mapping(self):
        if not self.has_mapping:
            return None
        mapping = self.proxymapping_set.first()
        return mapping

    def __str__(self):
        return self.proxy_uri

    def to_graph(self, include_mapping_target=False):
        g = Graph()
        subject = URIRef(self.proxy_uri)
        g.add((subject, RDF.type, URIRef('http://schemas.delving.eu/narthex/terms/ProxyResource')))
        g.add((subject, URIRef('http://schemas.delving.eu/narthex/terms/belongsTo'), URIRef(self.dataset.document_uri)))
        g.add((subject, URIRef('http://schemas.delving.eu/narthex/terms/proxyLiteralValue'),
               Literal(self.label, lang=self.language)))
        g.add((subject, URIRef('http://schemas.delving.eu/narthex/terms/proxyLiteralField'),
               URIRef(self.proxy_field.property_uri)))
        g.add((subject, URIRef('http://schemas.delving.eu/narthex/terms/skosFieldTag'),
               Literal(self.proxy_field.search_label)))
        g.add((subject, URIRef('http://schemas.delving.eu/narthex/terms/frequency'), Literal(self.frequency)))
        if self.has_mapping():
            mapping = self.get_mapping()
            g.add((subject, SKOS.exactMatch, URIRef(mapping.skos_concept_uri)))
            if include_mapping_target:
                g = g + mapping.get_mapping_target_graph()
        return g

    @staticmethod
    def get_proxy_resource_from_uri(proxy_uri: str, ds=None, original_label: str = None, store: RDFStore = None):
        if ProxyResource.objects.filter(proxy_uri=proxy_uri).exists():
            return ProxyResource.objects.get(proxy_uri=proxy_uri)

        if not store:
            store = rdfstore.get_rdfstore()
        query = """
        ?predicate ?object
        WHERE {{
         <{}> ?predicate ?object
        }}
        LIMIT 50
        """.format(proxy_uri)
        response = store.select(query=query)
        response_dict = {entry['predicate']['value']: entry['object']['value'] for entry in
                         response['results']['bindings']}
        if not response_dict:
            return ProxyResource.create_proxy_resource_from_uri(proxy_uri, original_label=original_label, ds=ds)
        proxy_literal_field = response_dict['http://schemas.delving.eu/narthex/terms/proxyLiteralField']
        proxy_literal_value = response_dict['http://schemas.delving.eu/narthex/terms/proxyLiteralValue']
        frequency = response_dict['http://schemas.delving.eu/narthex/terms/skosFrequency']
        ds = DataSet.get_dataset(document_uri=response_dict['http://schemas.delving.eu/narthex/terms/belongsTo'])
        proxy_field = ProxyResourceField.objects.filter(dataset=ds, property_uri=proxy_literal_field)
        if not proxy_field:
            proxy_field = ProxyResourceField(
                    property_uri=proxy_literal_field,
                    dataset_uri=ds.document_uri,
                    dataset=ds
            )
            proxy_field.save()
        else:
            proxy_field = proxy_field[0]
        resource_dict = {
            'proxy_uri': proxy_uri,
            'proxy_field': proxy_field,
            'dataset': ds,
            'frequency': frequency,
            'label': proxy_literal_value
        }
        proxy_resource, created = ProxyResource.objects.update_or_create(**resource_dict)
        return proxy_resource

    @staticmethod
    def create_proxy_resource_from_uri(uri: str, original_label: str = None, ds=None):
        extractor = re.compile("http://.*?/dataset/(.*?)/(.*?)/(.*)")
        spec, search_label, label = extractor.findall(uri)[0]
        if not ds:
            ds = DataSet.objects.get(spec=spec)
        proxy_field = ProxyResourceField.get_proxy_field(search_label, ds)
        resource_dict = {
            'proxy_uri': uri,
            'proxy_field': proxy_field,
            'dataset': ds,
            'frequency': 0,
            'label': original_label if original_label is not None else label
        }
        proxy_resource, created = ProxyResource.objects.update_or_create(**resource_dict)
        return proxy_resource

    @staticmethod
    def create_proxy_resource_uri(label: Literal, search_label: str, ds):
        clean_label = re.sub("[^\\w\\s-]", "", str(label))  # Remove all non-word, non-space or non-dash characters
        clean_label = re.sub('-', ' ', clean_label)  # Replace dashes with spaces
        clean_label = clean_label.strip()  # Trim leading/trailing whitespace (including what used to be leading/trailing dashes)
        clean_label = re.sub("\\s+", "-",
                             clean_label)  # Replace whitespace (including newlines and repetitions) with single dashes
        clean_label = clean_label.lower()  # Lowercase the final results

        if label.language:
            clean_label = "{}@{}".format(clean_label, label.language)
        proxy_resource_uri = "http://{base_url}/resource/dataset/{spec}/{search_label}/{label}".format(
                base_url=settings.RDF_BASE_URL.replace("http://", ""),
                spec=ds.spec,
                search_label=search_label,
                label=clean_label
        )
        return URIRef(proxy_resource_uri)

    @staticmethod
    def update_proxy_resource_uris(ds, graph: Graph):
        proxy_resources = []
        for proxy_field in ds.proxyresourcefield_set.all():
            for s, p, o in graph.triples((None, URIRef(proxy_field.property_uri), None)):
                if isinstance(o, Literal):
                    graph.remove((s, p, o))
                    proxy_field = ProxyResourceField.get_proxy_field_by_uri(str(p), ds)
                    proxy_resource_uri = ProxyResource.create_proxy_resource_uri(o, proxy_field.search_label, ds)
                    graph.add((s, p, proxy_resource_uri))
                    proxy_resource = ProxyResource.get_proxy_resource_from_uri(
                            proxy_uri=proxy_resource_uri,
                            original_label=str(o),
                            ds=ds
                    )
                else:
                    proxy_resource_uri = o
                    proxy_resource = ProxyResource.get_proxy_resource_from_uri(
                            proxy_uri=proxy_resource_uri,
                            ds=ds
                    )
                proxy_resources.append(proxy_resource)
        return set(proxy_resources), graph


@python_2_unicode_compatible
class DataSet(TimeStampedModel, GroupOwned):
    """

    There are four main types of datasets types:

    * Aggregated: data retrieved from Delving Narthex
    * Primary: data stored in custom models that implement the EDMRecordMappingType interface
    * Cached:
    * SKOS:
    *

    # TODO: implement MPTT nesting later
    """
    name = models.CharField(
            _("title"),
            max_length=512,
    )
    description = models.TextField(
            _("description"),
            blank=True
    )
    slug = AutoSlugField(
            _("slug"),
            populate_from='spec',
            overwrite=True
    )
    spec = models.CharField(
            _("spec name"),
            max_length=56,
            unique=True,
            help_text=_("spec name for the dataset")
    )
    document_uri = models.URLField(
            verbose_name=_("document_uri"),
            help_text=_("The document uri ")
    )
    named_graph = models.URLField(
            verbose_name=_("named_graph"),
            help_text=_("The named graph that this record belongs to")
    )
    dataset_type = ChoiceField(
            choices=DataSetType,
            verbose_name=_("Dataset Type"),
            default=DataSetType.aggregated,
            help_text=_("The type of the dataset"),
    )
    oai_pmh = ChoiceField(
            choices=OaiPmhPublished,
            verbose_name=_("OAI-PMH"),
            default=OaiPmhPublished.none,
            help_text=_("OAI-PMH harvestable"),
    )
    # description = RichText
    published = models.BooleanField(
            _("published"),
            default=True,
            help_text=_("Is this collection publicly available.")
    )
    data_owner = models.CharField(
            _("data_owner"),
            max_length=512,
    )
    total_records = models.IntegerField(
            _("total number of records"),
            default=0,
    )
    processed_records = models.IntegerField(
            _("total number of processed records"),
            default=0,
    )
    invalid = models.IntegerField(
            _("number of invalid records"),
            default=0,
    )
    valid = models.IntegerField(
            _("number of valid records"),
            default=0,
    )
    file_watch_directory = models.FilePathField(
            _("file watcher directory"),
            path="/tmp",  # todo later add spec_field
            blank=True,
            allow_folders=True,
            allow_files=False,
            help_text=_("The directory where this dataset looks for its digital objects to link")
    )
    process_key = models.CharField(
            _("process key"),
            help_text=_("Celery processing key. When present means that a synchronisation process is running"),
            null=True,
            blank=True,
            max_length=256
    )
    stay_in_sync = models.BooleanField(
            _("stay in sync with narthex"),
            default=True,
            help_text=_("Force unsynced state with Narthex")
    )
    records_in_sync = models.BooleanField(
            _("records in sync"),
            default=False,
            help_text=_("Keep records in sync with Narthex")
    )
    skos_in_sync = models.BooleanField(
            _("skos in sync"),
            default=False,
            help_text=_("Keep skos mappings in sync with Narthex")
    )
    sync_error_message = models.TextField(
            _("synchronisation error"),
            help_text=_("error message why synchronisation with the triple"
                        "store failed."),
            null=True,
            blank=True,
    )
    has_sync_error = models.BooleanField(
            _("has synchronisation error"),
            default=False
    )
    last_full_harvest_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    def get_spec(self):
        return self.spec

    @property
    def can_be_synchronised(self):
        return not self.records_in_sync and self.stay_in_sync and not self.sync_in_progress and not self.has_sync_error

    @property
    def sync_in_progress(self):
        return self.process_key not in ['', None]

    @staticmethod
    def get_first_graph_value(predicate, subject, graph):
        """Get the first value for a predicate in a graph. """
        predicate = predicate if isinstance(predicate, URIRef) else URIRef(predicate)
        subject = subject if isinstance(subject, URIRef) else URIRef(subject)
        return graph.value(subject=subject,
                           predicate=predicate,
                           any=True)

    @staticmethod
    def get_dataset(document_uri):
        if DataSet.objects.filter(document_uri=document_uri).exists():
            return DataSet.objects.filter(document_uri=document_uri).first()
        ds = DataSet.get_dataset_from_graph(dataset_graph_uri=document_uri)
        if not ds:
            raise ValueError("Unknown dataset with uri: {} ".format(document_uri))
        return ds

    @staticmethod
    def get_dataset_from_graph(store=None, graph=None, dataset_graph_uri=None):
        """Convert a  <http://schemas.delving.eu/narthex/terms/Dataset> to Dataset object. """

        def add_graph_name(ds):
            return ds if ds.endswith('/graph') else "{}/graph".format(ds.rstrip('/'))

        if dataset_graph_uri is None and graph is not None:
            dataset_graph_uri = graph.identifier

        if not store:
            store = rdfstore.get_rdfstore()

        if not graph:
            if not dataset_graph_uri:
                raise ValueError("when graph is None the dataset_graph_uri needs to be given")
            named_graph = add_graph_name(dataset_graph_uri)
            graph = store.get_graph_store.get(named_graph=named_graph, as_graph=True)
        subject = URIRef(dataset_graph_uri.replace('/graph', ''))
        if graph.value(subject=subject, predicate=RDF.type, any=True) != URIRef(
                'http://schemas.delving.eu/narthex/terms/Dataset'):
            return None
        value_of = partial(DataSet.get_first_graph_value, graph=graph, subject=subject)
        data_owner = value_of(predicate='http://schemas.delving.eu/narthex/terms/datasetOwner')
        spec = value_of(predicate='http://schemas.delving.eu/narthex/terms/datasetSpec')
        group, _ = Group.objects.get_or_create(name='dataset_admin')
        if not data_owner:
            data_owner = spec
        data_owner_group, _ = Group.objects.get_or_create(name=data_owner)
        # TODO add OAI-PMH and indexing
        update_values = {
            "description": value_of('http://schemas.delving.eu/narthex/terms/datasetDescription'),
            "name": value_of('http://schemas.delving.eu/narthex/terms/datasetName'),
            "dataset_type": DataSetType.aggregated,
            "total_records": value_of('http://schemas.delving.eu/narthex/terms/datasetRecordCount'),
            "invalid": value_of('http://schemas.delving.eu/narthex/terms/processedInvalid'),
            "valid": value_of('http://schemas.delving.eu/narthex/terms/processedValid'),
            "data_owner": data_owner,
            "document_uri": subject,
            "named_graph": graph.identifier,
            "last_full_harvest_date": value_of("http://schemas.delving.eu/narthex/terms/lastFullHarvestTime"),
        }
        for k, v in update_values.items():
            if k in ['total_records', 'invalid', 'valid'] and v is None:
                update_values[k] = 0
            if k in ['last_full_harvest_date'] and v is not None:
                update_values[k] = parser.parse(v)
        dataset, _ = DataSet.objects.update_or_create(spec=spec, defaults=update_values)
        dataset.groups.add(*[group, data_owner_group])
        ds_synced = value_of('http://schemas.delving.eu/narthex/terms/synced')
        if not ds_synced and store is not None:
            update_switch = QueryType.remove_insert.format(
                    named_graph=dataset.named_graph,
                    remove="?s <http://schemas.delving.eu/narthex/terms/synced> false",
                    insert="?s <http://schemas.delving.eu/narthex/terms/synced> true"
            )
            store.update(query="{}".format(update_switch))
        return dataset

    def generate_proxyfield_uri(self, label, language=None):
        label = label.replace(' ', '_')
        if language:
            label = "{}/{}".format(language, label)
        return "{}/resource/dataset/{}/{}".format(
                RDFRecord.get_rdf_base_url(prepend_scheme=True),
                self.spec,
                label
        )

    def update_graph_with_proxy_field(self, graph: Graph, proxy_field_uri: str):
        """# return graph, tuple_list with coined_uris, label, lang."""
        property_uri = URIRef(proxy_field_uri)
        fields = graph.subject_objects(predicate=property_uri)
        converted_literals = []
        for subject, obj in fields:
            if isinstance(obj, Literal):
                graph.remove((subject, property_uri, obj))
                new_uri = self.generate_proxyfield_uri(obj.value, obj.language)
                graph.add((subject, property_uri, URIRef(new_uri)))
                converted_literals.append((new_uri, obj))

        return graph, converted_literals

    @staticmethod
    def stage_for_indexing(dataset_graph_uri):
        """Set synced=false for all records that belong to the dataset."""
        store = rdfstore.get_rdfstore()
        query = """
        ?g where {{
            {{GRAPH ?g
                {{
                    ?s  <http://schemas.delving.eu/narthex/terms/belongsTo> <{}> .
                    ?s2 <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.openarchives.org/ore/terms/Aggregation>}} .
                  }}
        }}
        """.format(dataset_graph_uri)
        res = store.select(query=query)
        graph_list = [graph['g']['value'] for graph in res['results']['bindings']]
        update_switch = [QueryType.remove_insert.format(
                named_graph=g,
                remove="?s <http://schemas.delving.eu/narthex/terms/synced> true",
                insert="?s <http://schemas.delving.eu/narthex/terms/synced> false"
        ) for g in graph_list]
        store.update(query="\n".join(update_switch))
        return None

    def delete_from_index(self, index='{}'.format(settings.SITE_NAME)):
        """Delete all dataset records from the Search Index. """
        # TODO: use nested query for this to delete by spec and not only for the unfielded spec name
        response = es.delete_by_query(index=index, q="system.spec.raw:\"{}\"".format(self.spec))
        logger.info("Deleted {} from Search index with message: {}".format(self.spec, response))
        return response

    def _sparql_delete_all_query(self):
        delete_records = """DROP SILENT GRAPH <{graph_uri}>;
          DELETE {{
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }}
          WHERE {{
             GRAPH ?g {{
                ?foafDoc <http://xmlns.com/foaf/0.1/primaryTopic> ?record .
                ?foafDoc <http://schemas.delving.eu/narthex/terms/belongsTo>  <{dataset_uri}> .
                ?record a <http://schemas.delving.eu/narthex/terms/Record> .
             }}
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }};""".format(dataset_uri=self.document_uri, graph_uri=self.named_graph)
        return delete_records

    def _delete_dataset_records_in_rdfstore(self, store):
        """Only delete all records in the rdf store linked to this Dataset."""
        delete_records = self._sparql_delete_all_query()
        logger.info("Drop all graphs for dataset {}".format(self.spec))
        return store.update(query=delete_records)

    def delete_all_dataset_records(self, store):
        self._delete_dataset_records_in_rdfstore(store)
        self.delete_from_index()
        EDMRecord.objects.filter(dataset=self.id).delete()
        logger.info("Deleted all dataset records from Index, triple-store and database for {}".format(self.spec))
        return True

    def _delete_all_linked_triples(self, store):
        """Delete all Graphs linked to the dataset."""
        delete_graphs = """
          PREFIX foaf: <http://xmlns.com/foaf/0.1/>
          DROP SILENT GRAPH <{skos_graph_name}>;
          DELETE {{
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }}
          WHERE {{
             GRAPH ?g {{
                ?foafDoc foaf:PrimaryTopic ?record .
                ?foafDoc <http://schemas.delving.eu/narthex/terms/belongsTo>  <{dataset_uri}> .
                ?record a <http://schemas.delving.eu/narthex/terms/Record> .
             }}
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }};
          DELETE {{
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }}
          WHERE {{
             GRAPH ?g {{
                 ?subject <http://schemas.delving.eu/narthex/terms/mappingVocabulary> <{dataset_uri}> ;
                a <http://schemas.delving.eu/narthex/terms/TerminologyMapping>.
             }}
             GRAPH ?g {{
                ?s ?p ?o .
             }}
          }};
          DROP SILENT GRAPH <{dataset_graph_uri}>;""".format(
                dataset_uri=self.document_uri,
                dataset_graph_uri=self.named_graph,
                skos_graph_name=self.skosified_graph_uri
        )
        logger.info("Drop all graphs for dataset {}".format(self.spec))
        return store.update(query=delete_graphs)

    def _get_skosified_graph_uri(self, store):
        """Return the graph uri of the 'skosified' ProxyResources"""
        query = """
        select distinct ?g
        WHERE {{
            GRAPH ?g {{
                ?record <http://schemas.delving.eu/narthex/terms/belongsTo>  <{}>;
                 a <http://schemas.delving.eu/narthex/terms/ProxyResource> .

              }}
        }} limit 100""".format(self.document_uri)
        res = store.select(query=query)
        graph_list = [graph['g']['value'] for graph in res['results']['bindings']]
        return len(graph_list), graph_list

    @property
    def skosified_graph_uri(self):
        """The graph uri where all the skosifications are stored."""
        return "{}/skos/graph".format(self.document_uri)

    def _drop_skosified_graph(self, store):
        """Drop graph with all skosified or ProxyResources for the Dataset."""
        graphs = self._get_skosified_graph_uri(store)
        drop_queries = ["drop graph {}".format(graph) for graph in graphs]
        store.update(query="\n".join(drop_queries))
        logger.info("Drop all proxy resources graphs for dataset {}".format(self.spec))
        return len(graphs), graphs

    def delete_from_triple_store(self, store):
        """Delete all triples in the triple store that link back to the Dataset.

         * drop all record graphs
         * drop dataset/skos/graph
         * drop all skos mappings graphs  
        * drop dataset graph
        """
        try:
            self._delete_all_linked_triples(store)
        except Exception as ex:
            logger.error("Unable to clear all triples for dataset {} because of: {}".format(self.spec, ex))
            return False
        return True

    def delete_file_stores(self):
        """Delete all sources files and derivatives from the Nave Storage system. """
        ds_file_stores = [self.file_watch_directory, self.get_deepzoom_dir(), self.get_thumbnail_dir()]
        deleted = failed = []
        for store in ds_file_stores:
            try:
                shutil.rmtree(store)
                deleted.append(store)
            except FileNotFoundError as fnfe:
                failed.append(store)
                logger.info("Unable to delete store {} because of {}".format(store, fnfe))
        logger.info("deleted the following stores: {}.".format("; ".join(deleted)))
        return deleted, failed

    def get_deepzoom_dir(self):
        return os.path.join(settings.DEEPZOOM_BASE_DIR, self.spec)

    def get_thumbnail_dir(self):
        return os.path.join(settings.THUMBNAIL_BASE_DIR, self.spec)

    def mark_records_as_orphaned(self, state=True):
        """Mark all EDMRecords for a DataSet as orphaned or not.
        :param state: Where EDMRecords are orphaned or not.
        """
        EDMRecord.objects.filter(dataset=self).update(orphaned=state)

    @staticmethod
    def is_line_marker(line):
        m = re.match("<!--<(http://.*?graph)__(.*?)>-->", line)
        if not m:
            return False, None, None
        named_graph, content_hash = m.groups()
        return True, named_graph, content_hash

    def get_narthex_processed_fname(self):
        narthex_base = "~/NarthexFiles"
        return os.path.join(os.path.expanduser(narthex_base), settings.ORG_ID, "datasets", self.spec, "processed",
                            "00000.xml")

    def bulk_index(self, es_actions):
        logger.debug(es_actions)
        nr, errors = helpers.bulk(get_es(), es_actions)
        if nr > 0 and not errors:
            logger.info("Indexed records {} for dataset {}".format(nr, self.spec))
            return True
        elif errors:
            logger.error("Something went wrong with bulk index: {}".format(errors))
            return False
        return False

    def process_narthex_file(self, store=None, acceptance=False, path=None, console=False):

        if not store:
            store = rdfstore.get_rdfstore()

        if not path:
            processed_fname = self.get_narthex_processed_fname()
        else:
            processed_fname = path
        logger.info("started processing {} for dataset {}".format(processed_fname, self.spec))

        with open(processed_fname, 'r') as f:
            record = []
            lines = 0
            records = 0
            stored = 0
            new = 0
            not_orphaned = []
            bulk_insert_records = []
            sparql_update_queries = []
            es_actions = []
            # set orphaned records
            self.mark_records_as_orphaned(state=True)
            for line in f:
                lines += 1
                exists, named_graph, content_hash = self.is_line_marker(line)
                if exists:
                    edm_record = EDMRecord.objects.filter(source_hash=content_hash, named_graph=named_graph).exists()
                    if not edm_record:
                        triples = " ".join(record)
                        # print(is_marker)
                        new += 1
                        g = Graph(identifier=named_graph)
                        g.parse(data=triples)
                        if not EDMRecord.objects.filter(named_graph=named_graph).exists():
                            created_record = EDMRecord.graph_to_record(
                                    graph=g,
                                    ds=self,
                                    content_hash=None,
                                    acceptance=acceptance,
                                    bulk=True)

                            bulk_insert_records.append(created_record)

                            es_actions.append(
                                    created_record.create_es_action(
                                            action="index",
                                            store=store,
                                            context=False,  # todo: fix issue with context indexing later
                                            flat=True,
                                            exclude_fields=None,
                                            acceptance=acceptance
                                    )
                            )
                            if settings.RDF_STORE_TRIPLES:
                                sparql_update_queries.append(
                                    created_record.create_sparql_update_query(acceptance=acceptance))
                        else:
                            updated_record = EDMRecord.graph_to_record(
                                    graph=g,
                                    ds=self,
                                    content_hash=None,
                                    acceptance=acceptance
                            )
                            if settings.RDF_STORE_TRIPLES:
                                sparql_update_queries.append(
                                    updated_record.create_sparql_update_query(acceptance=acceptance))
                            es_actions.append(
                                    updated_record.create_es_action(
                                            action="index",
                                            store=store,
                                            context=False,  # todo: fix issue with context indexing later
                                            flat=True,
                                            exclude_fields=None,
                                            acceptance=acceptance
                                    )
                            )
                    else:
                        EDMRecord.objects.filter(source_hash=content_hash, named_graph=named_graph).update(
                                orphaned=False)
                        stored += 1
                    records += 1
                    record[:] = []
                    bulk_record_size = len(bulk_insert_records)
                    if bulk_record_size > 0 and bulk_record_size % 1000 == 0:
                        EDMRecord.objects.bulk_create(bulk_insert_records)
                        logger.info("inserted 1000 records of {} at {}".format(self.spec, time.ctime()))
                        bulk_insert_records[:] = []
                    nr_sparql_updates = len(sparql_update_queries)
                    if settings.RDF_STORE_TRIPLES and nr_sparql_updates > 0 and nr_sparql_updates % 50 == 0:
                        store.update("\n".join(sparql_update_queries))
                        sparql_update_queries[:] = []
                    if records % 1000 == 0:
                        logger.info("processed {} records of {} at {}".format(records, self.spec, time.ctime()))
                        if console:
                            print("processed {} records of {} at {}".format(records, self.spec, time.ctime()))
                        if len(es_actions) > 1000:
                            self.bulk_index(es_actions)
                            es_actions[:] = []
                else:
                    record.append(line)
            # store the remaining bulk items
            EDMRecord.objects.bulk_create(bulk_insert_records)
            self.bulk_index(es_actions)
            if settings.RDF_STORE_TRIPLES and len(sparql_update_queries) > 0:
                store.update("\n".join(sparql_update_queries))
            logger.info(
                    "Dataset {}: records inserted {}, records same content hash {}, lines parsed {}, total records processed {}".format(
                            self.spec, new, stored, lines, records)
            )
            return lines, records

    def remove_orphaned_records(self, store=None, acceptance=False):
        logger.info("Start removing orphans for dataset {}".format(self.spec))
        if not store:
            store = rdfstore.get_rdfstore()
        es_actions = []
        sparql_update_queries = []
        records_removed = 0
        for record in EDMRecord.objects.filter(dataset=self, orphaned=True):
            records_removed += 1
            es_actions.append(
                    record.create_es_action(
                            action="delete",
                            store=store,
                            context=False,  # todo: fix issue with context indexing later
                            flat=True,
                            exclude_fields=None,
                            acceptance=acceptance
                    )
            )
            if settings.RDF_STORE_TRIPLES:
                sparql_update_queries.append(record.create_sparql_update_query(delete=True, acceptance=acceptance))
            if len(sparql_update_queries) >= 50:
                store.update("\n".join(sparql_update_queries))
                sparql_update_queries[:] = []
            if len(es_actions) >= 1000:
                self.bulk_index( es_actions)
                es_actions[:] = []
        if settings.RDF_STORE_TRIPLES:
            store.update("\n".join(sparql_update_queries))
        if len(es_actions) > 0:
            self.bulk_index(es_actions)
        logger.info("Removed {} orphans for dataset {}".format(records_removed, self.spec))
        return records_removed


# @receiver(pre_delete, sender=DataSet)
def clean_all_related_nave_items(sender, instance, **kw):
    """
    Signal function to delete all traces of the dataset, its records and mappings from the Nave Storage System
    """
    from . import tasks
    store = rdfstore.get_rdfstore()
    tasks.delete_dataset_with_all_triples.delay(instance, store=store)


@python_2_unicode_compatible
class EDMRecord(RDFModel):
    """
    Persisting all records synchronised from the Metadata Manager
    """

    # todo replace with ContentType link
    dataset = models.ForeignKey(
            DataSet,
            verbose_name=_("dataset"),
            help_text=_("the dataset that this record belongs to"),
            related_name='%(app_label)s_%(class)s_related',
            related_query_name="record"
    )
    primary_source = models.ForeignKey(
            ContentType,
            blank=True,
            null=True,
            help_text=_("link to primary resource that implements EDMModel base class"))
    proxy_resources = models.ManyToManyField(ProxyResource, blank=True)
    rdf_in_sync = models.BooleanField(
            default=False
    )
    rdf_sync_error = models.TextField(null=True, blank=True)
    exclude_from_europeana = models.BooleanField(default=False)

    class Meta(object):
        verbose_name = _("Metadata Record")
        verbose_name_plural = _("Metadata Records")

    def save(self, *args, **kwargs):
        self.hub_id = self._generate_hub_id()
        super(EDMRecord, self).save(*args, **kwargs)

    def __str__(self):
        return self.document_uri

    def get_absolute_url(self):
        label = self.document_uri.split('resource/')[-1]
        return reverse('lod_page_detail', kwargs={'label': label})

    def get_graph(self, with_mappings=False, include_mapping_target=False, acceptance=False, target_uri=None):
        """Get Graph instance of this EDMRecord.

        :param target_uri: target_uri if you want a sub-selection of the whole graph
        :param acceptance: if the acceptance data should be listed
        :param include_mapping_target: Boolean also include the mapping target triples in graph
        :param with_mappings: Boolean integrate the ProxyMapping into the graph
        """
        rdf_string = self.source_rdf
        if acceptance and self.acceptance_rdf:
            rdf_string = self.acceptance_rdf

        graph = ConjunctiveGraph(identifier=self.named_graph)
        graph.namespace_manager = namespace_manager
        graph.parse(data=rdf_string, format='nt')
        if with_mappings:
            proxy_resources, graph = ProxyResource.update_proxy_resource_uris(self.dataset, graph)
            self.proxy_resources.add(*proxy_resources)
            for proxy_resource in proxy_resources:
                graph = graph + proxy_resource.to_graph(include_mapping_target=include_mapping_target)
        if target_uri and not target_uri.endswith("/about") and target_uri != self.document_uri:
            g = Graph(identifier=URIRef(self.named_graph))
            subject = URIRef(target_uri)
            for p, o in graph.predicate_objects(subject=subject):
                g.add((subject, p, o))
            graph = g
        return graph

    def get_spec_name(self):
        return self.dataset.spec

    def get_namespace_prefix(self):
        return "ore"

    def get_rdf_type(self):
        return "http://www.openarchives.org/ore/terms/Aggregation"

    def get_graph_mapping(self):
        return None

    @staticmethod
    def graph_to_record(graph, ds, bulk=False, content_hash=None, force_insert=False, acceptance=False):
        """Update or create an EDM record from a graph."""
        exclude_key = URIRef('http://schemas.delving.eu/nave/terms/excludedFromEuropeana')
        org_id = settings.ORG_ID
        spec = ds.spec
        identifier = re.sub("[/]+graph$", "", graph.identifier)
        local_id = identifier.split('/')[-1]
        hub_id = "{}_{}_{}".format(org_id, spec, local_id)
        exclude_from_europeana = RDFModel.get_first_literal(exclude_key, graph)
        if exclude_from_europeana is None:
            exclude_from_europeana = False
        elif not isinstance(exclude_from_europeana, bool):
            exclude_from_europeana = True if exclude_from_europeana.lower() in ['true'] else False

        if content_hash and not force_insert:
            query_filter = {'hub_id': hub_id}
            if acceptance:
                query_filter['acceptance_hash'] = content_hash
            else:
                query_filter['source_hash'] = content_hash
            if EDMRecord.objects.filter(**query_filter).exists():
                return None

        group, _ = Group.objects.get_or_create(name='dataset_admin')
        # get real identifier (support for with or without final slash)
        update_values = {
            "hub_id": hub_id,
            "dataset": ds,
            "named_graph": graph.identifier,
            "document_uri": identifier,
            "source_uri": identifier,
            "local_id": local_id,
            "rdf_in_sync": False,
            "rdf_sync_error": None,
            "orphaned": False,
            "exclude_from_europeana": exclude_from_europeana
        }
        # add content hash check
        if acceptance:
            update_values["acceptance_rdf"] = graph.serialize(format='nt', encoding="UTF-8")
            update_values["acceptance_updated"] = timezone.now().strftime(fmt)
            if content_hash:
                update_values['acceptance_hash'] = content_hash
        else:
            update_values["source_rdf"] = graph.serialize(format='nt', encoding="UTF-8")
            update_values["source_updated"] = timezone.now().strftime(fmt)
            if content_hash:
                update_values['source_hash'] = content_hash
        if not bulk:
            edm_record, _ = EDMRecord.objects.update_or_create(hub_id=hub_id, defaults=update_values)
            edm_record.groups.add(*ds.groups.all())
        else:
            update_values['hub_id'] = hub_id
            edm_record = EDMRecord(**update_values)
        return edm_record


# @receiver(post_save, sender=EDMRecord)
# def update_in_index(sender, instance, **kw):
#     from lod import tasks
#     tasks.store_graph.apply_async(
#         [instance],
#         routing_key=settings.RECORD_QUEUE,
#         queue=settings.RECORD_QUEUE,
#         # compression='zlib'
#     )
#     tasks.update_rdf_in_index.apply_async(
#         [instance],
#         routing_key=settings.RECORD_QUEUE,
#         queue=settings.RECORD_QUEUE,
#         # compression='zlib'
#     )
#
#
# @receiver(pre_delete, sender=EDMRecord)
# def remove_from_index(sender, instance, **kw):
#     from lod import tasks
#     tasks.delete_rdf_resource.delay(instance)
#     tasks.remove_rdf_from_index.delay(instance)
#
#
# class EDMBaseModel(TimeStampedModel):
#     content_type = models.ForeignKey(ContentType)
#     object_id = models.PositiveIntegerField()
#     content_object = GenericForeignKey('content_type', 'object_id')
#
#     class Meta(object):
#         abstract = True
