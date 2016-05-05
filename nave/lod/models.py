# -*- coding: utf-8 -*- 
"""
This model contains the functionality to save SPARQL queries that can be used in the
'/snorql' SPARQL query explorer to provide the user with some example queries.


TODO: create model for external SPARQL-Endpoints that can be used via a proxy in the SNORQL app.
"""
import datetime
import logging
from urllib.parse import quote

from celery import chain
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import AutoSlugField, UUIDField
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel
from rdflib import Namespace, ConjunctiveGraph, URIRef, Literal, BNode, Graph
from rdflib.namespace import RDFS, RDF, FOAF, DC, DCTERMS, OWL
from rdflib.plugins.serializers.nquads import _nq_row

from lod import namespace_manager, RDF_BASE_URL, get_rdf_base_url
from lod.namespace import NAVE
from lod.utils import rdfstore
from lod.utils.edm import GraphBindings
from lod.utils.lod import get_cache_url, get_remote_lod_resource, store_remote_cached_resource, get_geo_points, \
    get_graph_statistics

fmt = '%Y-%m-%d %H:%M:%S%z'  # '%Y-%m-%d %H:%M:%S %Z%z'

logger = logging.getLogger(__name__)


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
        related_name="%(app_label)s_%(class)s_related"
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name=_("Group"),
        help_text=_("The groups that have access to this metadata record"),
        blank=True,
        related_name="%(app_label)s_%(class)s_related"
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


class TitleDescriptionModel(models.Model):
    """ TitleDescriptionModel
    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.
    """
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        abstract = True


class RDFSubjectLookUp(TimeStampedModel):
    # todo: decide how to deal with subjects created in multiple graphs like EDM:Agent

    subject_uri = models.URLField(unique=True, max_length=512)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta(object):
        verbose_name = _("RDF Subject LookUp")
        verbose_name_plural = _("RDF Subject LookUp")

    def __str__(self):
        return self.subject_uri


class RDFModel(TimeStampedModel, GroupOwned):
    """Basic model for each Django Model that implements an RDF interface.

    The basic design is that it saves one whole named Graph.

    """
    slug_field = 'hub_id'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_uri = r'{}/resource'.format(get_rdf_base_url(prepend_scheme=True))
        if self.get_namespace_prefix():
            self.ns = Namespace('http://{}/resource/ns/{}/'.format(RDF_BASE_URL.replace("http://", ""), self.get_namespace_prefix()))
            self.rdf_type_base = Namespace("{}/{}/".format(self.base_uri, self.get_rdf_type().lower()))
            namespace_manager.bind(self.get_namespace_prefix(), self.ns)
        self.ns_dict = dict(list(namespace_manager.namespaces()))
        self.graph = None

    hub_id = models.CharField(
        _("hub id"),
        max_length=512,
        unique=True,
        help_text=_("legacy culture hubId for documents")
    )
    slug = AutoSlugField(
        _('slug'),
        populate_from=slug_field,
        max_length=512
    )
    document_uri = models.URLField(
        verbose_name=_("document_uri"),
        unique=True,
        help_text=_("The document uri or cache uri ")
    )
    named_graph = models.URLField(
        verbose_name=_("named_graph"),
        help_text=_("The named graph that this record belongs to")
    )
    local_id = models.CharField(
        verbose_name=_("local identifier"),
        max_length=512,
        help_text=_("The local identifier supplied by the provider")
    )
    uuid = UUIDField(
        verbose_name=_("uuid"),
        help_text=_("The unique uuid created on first save")
    )
    source_uri = models.URLField(
        verbose_name=_("source uri"),
        blank=True,
        null=True,
        help_text=_("If the item is cached this is the original uri where this object is found. It is also saved "
                    "in the graph as owl:sameAs")
    )
    acceptance_rdf = models.TextField(
            verbose_name=_("acceptance rdf"),
            blank=True,
            help_text=_("The rdf stored in the ntriples (nt) format. ")
    )
    acceptance_hash = models.CharField(
            verbose_name=_("acceptance hash"),
            max_length=512,
            unique=True,
            blank=True,
            null=True,
            help_text=_("The sha1 content has of the stored ntriples.")
    )
    acceptance_updated = models.DateTimeField(
            verbose_name=_("acceptance update date"),
            default=timezone.now,
            blank=True,
            null=True,
            help_text=_("The date the acceptance source was updated")
    )
    source_rdf = models.TextField(
        verbose_name=_("production rdf"),
        blank=True,
        help_text=_("The rdf stored in the ntriples (nt) format. ")
    )
    source_hash = models.CharField(
        verbose_name=_("source hash"),
        max_length=512,
        unique=True,
        blank=True,
        null=True,
        help_text=_("The sha1 content has of the stored ntriples.")
    )
    source_updated = models.DateTimeField(
        verbose_name=_("production update date"),
        default=timezone.now,
        blank=True,
        null=True,
        help_text=_("The date the source was updated")
    )
    has_store_error = models.BooleanField(
        verbose_name=_("has store error"),
        default=False,
        help_text=_("If post save actions have thrown an error.")
    )
    error_message = models.TextField(
        verbose_name=_("error message"),
        blank=True,
        null=True
    )
    # TODO: currently the marking as orphan is not fully implemented. It needs to be tested with the BULK API update
    # mechanism
    orphaned = models.BooleanField(default=False)
    subjects = GenericRelation(RDFSubjectLookUp)

    def _pre_save(self):
        self.hub_id = self._generate_hub_id()
        if not self.document_uri:
            self.document_uri = self._get_document_uri()
        if not self.source_uri:
            self.source_uri = self._get_document_uri()
        if not self.named_graph:
            self.named_graph = self._generate_namedgraph_uri()

    def save(self, *args, **kwargs):
        self._pre_save()
        super(RDFModel, self).save(*args, **kwargs)

    @staticmethod
    def create_rdf_content_hash(rdf_as_string):
        import hashlib
        hash_object = hashlib.sha1(rdf_as_string.encode('utf-8'))
        return hash_object.hexdigest()

    def __str__(self):
        return self.document_uri

    def get_absolute_uri(self):
        label = self.document_uri.split('resource/')[-1]
        return reverse('lod_page_detail', kwargs={'label': label})

    def get_spec_name(self):
        """Implement the set name for this record. """
        raise NotImplementedError("Configure the spec name for this record.")

    def get_slug_field(self):
        """The field to use for generating the AutoSlug. """
        return self.slug_field

    def get_rdf_type(self):
        """The rdf type of this record."""
        raise NotImplementedError("Configure the RDF type of this record.")

    def get_namespace_prefix(self):
        """The namespace prefix for this record."""
        raise NotImplementedError("Configure a namespace that is auto generated for this model")

    def get_graph_mapping(self):
        """ A defaultdict(list) with predicate as key and objects als list."""
        raise NotImplementedError("Supply a mapping dictionary")

    def _generate_hub_id(self):
        return "{}_{}_{}".format(settings.ORG_ID, self.get_spec_name(), self.local_id)

    def create_sparql_update_query(self, delete=False, acceptance=False):
        source_rdf = self.source_rdf if not acceptance else self.acceptance_rdf
        rdf_triples = source_rdf if not isinstance(source_rdf, bytes) else source_rdf.decode('utf-8')
        sparql_update = """DROP SILENT GRAPH <{graph_uri}>;
        INSERT DATA {{ GRAPH <{graph_uri}> {{
            {triples}
            }}
        }};
        """.format(
            graph_uri=self.named_graph,
            triples=rdf_triples
        )
        if delete:
            sparql_update = """DROP SILENT GRAPH <{graph_uri}>;""".format(graph_uri=self.named_graph)
        return sparql_update

    @staticmethod
    def graph_to_record(graph, ds, bulk=False, content_hash=None, force_insert=False, acceptance=False):
        raise NotImplementedError("Supply a method that turns a graph into a record")

    @staticmethod
    def get_first_literal(predicate, graph):
        if not isinstance(predicate, URIRef):
            predicate = URIRef(predicate)
        for s, o in graph.subject_objects(predicate=predicate):
            if isinstance(o, Literal):
                if o.datatype == URIRef('http://www.w3.org/2001/XMLSchema#boolean'):
                    return True if o.value in ['true', 'True'] else False
                elif o.datatype == URIRef('http://www.w3.org/2001/XMLSchema#integer'):
                    return int(o.value)
                else:
                    return o.value
        return None

    def _get_document_uri(self):
        if not self.document_uri:
            if self.source_uri:
                self.document_uri = self.document_uri
            else:
                self.document_uri = "{}/{}/{}/{}".format(self.base_uri, self.get_rdf_type(), self.get_spec_name(),
                                                     self.local_id)
        return self.document_uri

    def _generate_namedgraph_uri(self):
        graph__format = "{}/graph".format(self.source_uri.rstrip('/'))
        return graph__format

    def _generate_about_uri(self):
        return "{}/about".format(self.source_uri.rstrip('/'))

    def get_attribution_name(self):
        """The CC attribution name for this record."""
        return self.get_spec_name()

    @staticmethod
    def get_first_graph_value(predicate, graph):
        """Get the first value for a predicate in a graph. """
        predicate = predicate if isinstance(predicate, URIRef) else URIRef(predicate)
        return graph.value(subject=graph.identifier,
                           predicate=predicate,
                           any=True)

    class Meta(object):
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)
        abstract = True

    def _add_about_triples(self, about):
        subject = URIRef(self._generate_about_uri())
        about.add((subject, RDF.type, FOAF.Document))
        about.add((subject, FOAF.primaryTopic, URIRef(self.source_uri)))
        about.add((subject, DCTERMS.created, Literal(self.created, datatype="xsd:date")))
        about.add((subject, DCTERMS.modified, Literal(self.modified, datatype="xsd:date")))
        cc = Namespace('http://creativecommons.org/ns#')
        about.add((subject, cc.license, URIRef('http://creativecommons.org/licenses/by/3.0/')))
        about.add((subject, cc.attributionURL, URIRef(self.source_uri)))
        about.add((subject, cc.attributionName, Literal(self.get_attribution_name())))
        about.add((subject, NAVE.hubId, Literal(self.hub_id)))
        return about

    def _populate_graph(self):
        graph = ConjunctiveGraph(identifier=self._generate_namedgraph_uri())
        graph.namespace_manager = namespace_manager
        subject = URIRef(self._get_document_uri())
        graph.add((subject, RDFS.isDefinedBy, URIRef(self._generate_about_uri())))
        self._add_about_triples(graph)
        graph.add((subject, RDF.type, self.ns[self.get_rdf_type()]))
        if self.source_uri and self.source_uri != self.document_uri:
            graph.add((subject, OWL.sameAs, URIRef(self.source_uri)))
        for key, value in self.get_graph_mapping().items():
            if isinstance(key, URIRef):
                predicate = key
            elif isinstance(key, str) and key.startswith('http://'):
                predicate = URIRef(key)
            elif isinstance(key, str) and ":" in key:
                ns, label = key.split(":")
                ns = self.ns_dict.get(ns)
                predicate = URIRef("{}/{}".format(str(ns).rstrip('/'), label))
            else:
                raise ValueError("unknown predicate key in mapping dict: {}".format(key))
            if type(value) in [str, float, int] and value:
                if isinstance(value, str) and any([value.startswith(uri_prefix) for uri_prefix in ["http", "urn"]]):
                    value = URIRef(value)
                else:
                    value = Literal(value)
            elif type(value) in [Literal, URIRef]:
                value = value
            else:
                logger.warn("Unsupported datatype {} for value {}".format(type(value), value))
            if value:
                graph.add((subject, predicate, value))
        graph.namespace_manager = namespace_manager
        return graph

    def get_graph(self, acceptance=False, target_uri=None):
        if not self.graph:
            self.graph = Graph(identifier=URIRef(self.named_graph))
            self.graph.namespace_manager = namespace_manager
            if acceptance and self.acceptance_rdf:
                self.graph.parse(data=self.acceptance_rdf, format="nt")
            elif self.source_rdf:
                self.graph.parse(data=self.source_rdf, format="nt")
            else:
                self.graph = self._populate_graph()
            if target_uri and target_uri != self.document_uri:
                g = Graph(identifier=URIRef(self.named_graph))
                subject = URIRef(target_uri)
                for p, o in self.graph.predicate_objects(subject=subject):
                    g.add((subject, p, o))
                self.graph = g
        return self.graph

    def get_nquads_string(self):
        graph = self.get_graph()
        nquads = []
        for triple in graph:
            nquads.append(_nq_row(triple, graph.identifier))
        return "".join(nquads)

    def get_triples(self, acceptance=False):
        # todo use switch between acceptance or production
        source_rdf = self.acceptance_rdf if acceptance and self.acceptance_rdf else self.source_rdf
        return source_rdf.decode('utf-8'), self.named_graph

    def _generate_doc_type(self):
        return "{}_{}".format(self.__class__._meta.app_label, self.__class__._meta.model_name)

    @staticmethod
    def get_object_from_sparql_result(value_dict):
        if len(list(value_dict.keys())) == 1:
            value_dict = list(value_dict.values())[0]
        obj_type = value_dict.get('type', "literal")
        if obj_type == "literal" or obj_type == "typed-literal":
            language = value_dict['xml:lang'] if "xml:lang" in value_dict else None
            datatype = value_dict['datatype'] if "datatype" in value_dict else None
            obj = Literal(
                value_dict['value'],
                lang=language,
                datatype=datatype
            )
        elif obj_type == "uri":
            obj = URIRef(value_dict['value'])
        elif obj_type == "bnode":
            obj = None
        return obj

    @staticmethod
    def get_context_levels(nr_vars):
        return int(((nr_vars - 3) / 2) + 1)

    @staticmethod
    def get_context_triples(sparql_vars):
        nr_vars = len(sparql_vars)
        levels = RDFModel.get_context_levels(nr_vars)
        triples = []
        for level in range(int(levels)):
            triples.append(tuple(sparql_vars[:3]))
            sparql_vars = sparql_vars[2:]
        return triples

    @staticmethod
    def get_graph_from_sparql_results(sparql_json, named_graph=None):
        if len(sparql_json['results']['bindings']) == 0:
            return ConjunctiveGraph(), 0
        sparql_vars = sparql_json['head']['vars']
        if 'g' in sparql_vars:
            if not named_graph:
                named_graph = sparql_json['results']['bindings'][0]['g']['value']
            sparql_vars.remove('g')
        triple_levels = RDFModel.get_context_triples(sparql_json['head']['vars'])
        nr_levels = len(triple_levels)
        if named_graph:
            named_graph = URIRef(named_graph)
        graph = ConjunctiveGraph(identifier=named_graph)

        graph.namespace_manager = namespace_manager
        for binding in sparql_json['results']['bindings']:
            binding_levels = RDFModel.get_context_levels(len(binding.keys()))
            for s, p, o in triple_levels[:binding_levels]:
                subject = URIRef(binding[s]['value'])
                if binding[s]['type'] == 'bnode':
                    subject = BNode(binding[s]['value'])
                predicate = URIRef(binding[p]['value'])
                obj = RDFModel.get_object_from_sparql_result(binding[o])
                graph.add((subject, predicate, obj))
        # materialize inferences
        for subject, obj in graph.subject_objects(
                predicate=URIRef("http://www.openarchives.org/ore/terms/isAggregatedBy")):
            graph.add((obj, URIRef("http://www.openarchives.org/ore/terms/aggregates"), subject))
            graph.remove((subject, URIRef("http://www.openarchives.org/ore/terms/isAggregatedBy"), obj))
        return graph, nr_levels

    @staticmethod
    def get_describe_graph(store, named_graph=None, target_uri=None):
        bind = ""
        if not named_graph:
            named_graph_param = "?g"
        else:
            named_graph_param = "<{}>".format(named_graph)
        if target_uri:
            bind = "BIND(<{}> as ?s)".format(target_uri)
        query = """SELECT  *
                WHERE
                  {{
                  {bind}
                  GRAPH {named_graph}
                      {{ ?s ?p ?o}}
                  }}
                LIMIT   500
           """.format(named_graph=named_graph_param, bind=bind)
        response = store.query(query=query)
        return RDFModel.get_graph_from_sparql_results(response, named_graph=named_graph)

    @staticmethod
    def get_context_graph(store, named_graph=None, target_uri=None):
        bind = ""
        if not named_graph:
            named_graph_param = "?g"
        else:
            named_graph_param = "<{}>".format(named_graph)
        if target_uri:
            bind = "BIND(<{}> as ?s)".format(target_uri)
        query = """SELECT  *
                WHERE
                  {{
                  {bind}
                  GRAPH {named_graph}
                      {{ ?s ?p ?o}}
                    OPTIONAL
                      {{ ?o ?p2 ?o2 ;
                          a <http://schemas.delving.eu/narthex/terms/ProxyResource> .
                        OPTIONAL
                          {{ ?o2 ?p3 ?o3 . NOT EXISTS {{ ?o2 a  <http://schemas.delving.eu/narthex/terms/Dataset> . }}
                          }}
                      }}
                  }}
                LIMIT   500
           """.format(named_graph=named_graph_param, bind=bind)
        # todo add additional clauses
        #  OPTIONAL
        # {{ ?o ?p2 ?o2 ;
        # a <http://www.openarchives.org/ore/terms/Aggregation> .
        # OPTIONAL
        # {{ ?o2 ?p3 ?o3 . NOT EXISTS {{ ?o2 a  <http://schemas.delving.eu/narthex/terms/Dataset> . }}
        # }}
        # }}
        response = store.query(query=query)
        return RDFModel.get_graph_from_sparql_results(response, named_graph)

    @staticmethod
    def get_skos_context_graph(store, target_uri):
        query = """
        SELECT distinct *
        WHERE {{
            BIND(<{}> AS ?s)

            {{ ?s ?p ?o}}
            BIND(( <http://www.w3.org/2004/02/skos/core#prefLabel> || <http://www.w3.org/2004/02/skos/core#altLabel> ) AS ?p2)
            OPTIONAL
              {{ ?o ?p2 ?o2 }}
        }}
        """.format(target_uri)
        response = store.query(query=query)
        return RDFModel.get_graph_from_sparql_results(response)

    @staticmethod
    def get_nav_tree(store, target_uri):
        # todo still implement based on
        sparql_result = RDFModel.get_skos_broader_context_graph(store, target_uri=target_uri)
        pass

    @staticmethod
    def get_skos_broader_context_graph(store, target_uri):
        query = """
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT distinct ?s ?p ?o ?broader ?prefLabel
        WHERE {{
          bind(<{}> as ?s)
          {{
              ?s skos:broader* ?broader .
              FILTER ( ?s != ?broader ) .
              ?broader skos:prefLabel ?prefLabel .
          }}
          union
          {{
            ?s ?p ?o .
              Optional {{
                    ?o skos:prefLabel ?prefLabel
                }}
             }}
        }}
        LIMIT 100
        """.format(target_uri)
        response = store.query(query=query)
        return response

    def create_es_action(self, action="index", record_type=None, index=settings.SITE_NAME, store=None, doc_type=None,
                         context=True, flat=True, exclude_fields=None, acceptance=False):
        if doc_type is None:
            doc_type = self._generate_doc_type()
        if record_type is None:
            record_type = self.get_rdf_type()
        if not store:
            store = rdfstore.get_rdfstore()

        if acceptance:
            index = "{}_acceptance".format(index)

        if record_type == "http://www.openarchives.org/ore/terms/Aggregation":
            record_type = "mdr"

        if action == "delete":
            return {
                '_op_type': action,
                '_index': index,
                '_type': doc_type,
                '_id': self.hub_id
            }

        graph = None

        if not context:
            graph = self.get_graph()
        else:
            graph, nr_levels = self.get_context_graph(store=store, named_graph=self.named_graph)
            graph.namespace_manager = namespace_manager

        bindings = GraphBindings(
            about_uri=self.source_uri,
            graph=graph
        )
        index_doc = bindings.to_flat_index_doc() if flat else bindings.to_index_doc()
        if exclude_fields:
            index_doc = {k: v for k, v in index_doc.items() if k not in exclude_fields}
        # add delving spec for default searchability
        index_doc["delving_spec"] = [
            {'@type': "Literal",
             'value': self.get_spec_name(),
             'raw': self.get_spec_name(),
             'lang': None}
        ]
        logger.info(index_doc)
        mapping = {
            '_op_type': action,
            '_index': index,
            '_type': doc_type,
            '_id': self.hub_id,
            '_source': index_doc
        }
        thumbnail = bindings.get_about_thumbnail
        mapping['_source']['system'] = {
            'slug': self.slug,
            'thumbnail': thumbnail if thumbnail else "",
            'preview': "detail/foldout/{}/{}".format(doc_type, self.slug),
            'caption': bindings.get_about_caption if bindings.get_about_caption else "",
            'about_uri': self.document_uri,
            'source_uri': self.source_uri,
            'created_at': datetime.datetime.now().isoformat(),
            'modified_at': datetime.datetime.now().isoformat(),
            'source_graph': graph.serialize(format='nt', encoding="utf-8").decode(encoding="utf-8"),
            'proxy_resource_graph': None,
            'web_resource_graph': None,
            # 'about_type': [rdf_type.qname for rdf_type in bindings.get_about_resource().get_types()]
            # 'collections': None, todo find a way to add collections via link
        }
        data_owner = self.dataset.data_owner if hasattr(self, 'dataset') else None
        dataset_name = self.dataset.name if hasattr(self, 'dataset') else None
        mapping['_source']['legacy'] = {
            'delving_hubId': self.hub_id,
            'delving_recordType': record_type,
            'delving_spec': self.get_spec_name(),
            'delving_owner': data_owner,
            'delving_orgId': settings.ORG_ID,
            'delving_collection': dataset_name,
            'delving_title': self.get_first_literal(DC.title, graph),
            'delving_creator': self.get_first_literal(DC.creator, graph),
            'delving_description': self.get_first_literal(DC.description, graph),
            'delving_provider': index_doc.get('edm_provider')[0].get('value') if 'edm_provider' in index_doc else None,
            'delving_hasGeoHash': "true" if bindings.has_geo() else "false",
            'delving_hasDigitalObject': "true" if thumbnail else "false",
            'delving_hasLandingePage': "true" if 'edm_isShownAt' in index_doc else "false",
            'delving_hasDeepZoom': "true" if 'nave_deepZoom' in index_doc else "false",
        }
        return mapping

    @staticmethod
    def get_geo_points(graph):
        return get_geo_points(graph)

    @staticmethod
    def get_graph_statistics(graph):
        return get_graph_statistics(graph)

    def get_all_subjects_from_graphs(self):
        production = self.get_graph()
        acceptance = self.get_graph(acceptance=True)
        combined_graph = production + acceptance
        return {s.toPython() for s in set(combined_graph.subjects()) if isinstance(s, URIRef)}

    def update_linked_subjects(self):
        linked_subjects = {s.subject_uri for s in self.subjects.all()}
        graph_subjects = self.get_all_subjects_from_graphs()
        added = graph_subjects.difference(set(linked_subjects))
        logger.debug("Subject Links added: {}".format(added))
        removed = set(linked_subjects).difference(graph_subjects)
        logger.debug("Subject Links removed: {}".format(removed))
        for s in added:
            RDFSubjectLookUp.objects.update_or_create(subject_uri=s, defaults={'content_object': self})
        for s in removed:
            RDFSubjectLookUp.objects.filter(subject_uri=s).delete()

    def get_enrichments(self):
        """Return all linked UserGeneratedContent Objects."""
        return UserGeneratedContent.objects.filter(source_uri=self.document_uri)


class RDFModelTest(RDFModel):
    """ Model used for unit testing only.
    """

    @staticmethod
    def graph_to_record(graph, ds, bulk=False, content_hash=None, force_insert=False):
        pass

    def get_graph_mapping(self):
        mappings = {
            'dc:identifier': self.local_id,
            DC.title: "test title"
        }
        return mappings

    def get_namespace_prefix(self):
        return "test"

    def get_spec_name(self):
        return "test_spec"

    def get_rdf_type(self):
        return "Document"


class UserGeneratedContent(GroupOwned, TimeStampedModel):
    """Model for enrichments created by Users via a form on the Detail pages."""
    source_uri = models.URLField(
        verbose_name=_("RDF source URI"),
    )
    link = models.URLField(
        verbose_name=_("External link")
    )
    name = models.CharField(
        verbose_name=_("name"),
        blank=False,
        null=False,
        max_length=128
    )
    short_description = models.CharField(
        verbose_name=_("short description"),
        blank=False,
        null=False,
        max_length=512
    )
    content_type = models.CharField(
        verbose_name=_("content_type"),
        blank=False,
        null=False,
        max_length=64,
        help_text=_("The content type of the link, e.g. wikipedia or youtube.")
    )
    html_summary = models.TextField(
        verbose_name=_("html summary"),
        blank=True,
        null=True,
        help_text=_("Contains the unfurled HTML from the saved link")
    )
    published = models.BooleanField(
        verbose_name=_("published"),
        default=True,
        help_text=_("Should the UGC be published to unauthorised users.")
    )

    class Meta:
        unique_together = ("source_uri", "link")
        verbose_name = _("User Generated Content")
        verbose_name_plural = _("User Generated Content")

    def __str__(self):
        return "{} linked to {}".format(self.link, self.source_uri)

    def save(self, *args, **kwargs):
        # point to resource and not page or data
        source_uri = self.source_uri.replace('/data/', '/resource/').replace('/page/', '/resource/')
        # rewrite to base url
        from lod.utils.lod import get_internal_rdf_base_uri
        self.source_uri = get_internal_rdf_base_uri(source_uri)
        super(UserGeneratedContent, self).save(*args, **kwargs)


class RDFPrefix(TitleSlugDescriptionModel, TimeStampedModel):
    """
    The RDF prefixes that be used to construct and save SPARQL queries
    """
    prefix = models.CharField(_("prefix"), max_length=25, unique=True)
    uri = models.URLField(_("prefix url"))

    class Meta(object):
        verbose_name = _("RDF Prefix")
        verbose_name_plural = _("RDF Prefixes")

    def __str__(self):
        return self.title

    def formatted(self):
        return "PREFIX {prefix}: <{uri}>".format(prefix=self.prefix, uri=self.uri)

    def as_namespace(self):
        return 'xmlns:{0}="{1}"'.format(self.prefix, self.uri)

    def as_sparql_prefix(self):
        return "PREFIX {0}: <{1}>".format(self.prefix, self.uri)


class SPARQLQuery(TitleSlugDescriptionModel, TimeStampedModel):
    """
    The SPARQL queries that are stored as examples for re-use by the Users
    """
    prefixes = models.ManyToManyField(RDFPrefix, verbose_name=_('prefixes'))
    query = models.TextField(_("SPARQL query"))

    class Meta(object):
        verbose_name = _("SPARQL Query")
        verbose_name_plural = _("SPARQL Queries")

    def __str__(self):
        return self.title

    def formatted(self):
        prefix_list = '\n'.join([prefix.formatted() for prefix in self.prefixes.all()])
        return "{prefixes}\n{query}".format(prefixes=prefix_list, query=self.query)


class SPARQLUpdateQuery(TitleSlugDescriptionModel, TimeStampedModel):
    """
    The SPARQL update queries that will be executed periodically with insert or construct queries to
     add enrichments to the existing records
    """
    prefixes = models.ManyToManyField(RDFPrefix, verbose_name=_('prefixes'))
    query = models.TextField(_("SPARQL query"))
    active = models.BooleanField(_("active"), default=False, help_text=_("If the SPARQL update query is scheduled for "
                                                                         "periodic execution."))

    class Meta(object):
        verbose_name = _("SPARQL Update Query")
        verbose_name_plural = _("SPARQL Update Queries")

    def __str__(self):
        return self.title

    def formatted(self):
        prefix_list = '\n'.join([prefix.formatted() for prefix in self.prefixes.all()])
        return "{prefixes}\n{query}".format(prefixes=prefix_list, query=self.query)


class ResourceCacheTarget(TimeStampedModel):
    """Contains the RDF resource target information of caching remote LoD data.

    When this class in initialised it will also try to retrieve the classes and properties
    either from the SPARQL endpoint or from the link to the ontology.

    The classes and properties then can be selected so that only these are cached and a clean view
    on the cached resource can be presented.

    """

    name = models.CharField(
        verbose_name=_("name"),
        max_length=256,
        help_text=_("The name of the remote resource")
    )
    base_url = models.URLField(
        _("base_url"),
        unique=True,
        help_text=_("The base url of the LoD target")
    )
    sparql_endpoint = models.URLField(
        verbose_name=_("sparql endpoint"),
        blank=True,
        null=True,
        help_text=_("The sparql endpoint")
    )
    ontology_url = models.URLField(
        verbose_name=_("ontology url"),
        blank=True,
        null=True,
        help_text=_("The link to an RDF version of the Ontology")
    )


# class DataSetFieldLink(TimeStampedModel):
#
#     spec = models.CharField(
#         _("spec"),
#         max_length=256,
#         blank=True,
#         null=True,
#         help_text=_("the spec name that the literal value belongs to")
#     )
#     literal_value = models.CharField(
#         _("literal value"),
#         max_length=256
#     )
#     literal_property = models.CharField(
#         _("literal property"),
#         max_length=256,
#     )
#     cache_url = models.CharField(
#         _("cache_url"),
#         max_length=256,
#     )


class CacheResource(RDFModel):
    """Storage for remote cached LoD resources."""
    stored = models.BooleanField(
        _("stored"),
        default=False
    )
    # cachable = models.BooleanField(
    #     _("cachable"),
    #     default=False,
    #     help_text=_("remote resource is cacheable")
    # )

    # link source_field
    # document_uri = cache_url
    # named graph chache_uri + # graph

    def get_namespace_prefix(self):
        return "lod"

    def get_rdf_type(self):
        return "Cached"

    def get_spec_name(self):
        return "cache"

    def get_graph_mapping(self):
        return {}

    def save(self, *args, **kwargs):
        self.local_id = quote(self.source_uri)
        self.hub_id = self._generate_hub_id() + "#cached"
        if not self.document_uri:
            if self.source_uri:
                self.document_uri = self.source_uri
            else:
                self.document_uri = self.get_cache_url(self.source_uri)
        if not self.named_graph:
            self.named_graph = self._generate_namedgraph_uri()
        super(RDFModel, self).save(*args, **kwargs)

    def update_cached_resource(self, graph_store):
        resource = self.get_remote_lod_resource(self.source_uri)
        response = self.store_remote_cached_resource(
            graph=resource,
            graph_store=graph_store,
            named_graph=self.get_named_graph()
        )
        if not response:
            stored = False
        else:
            stored = True
        CacheResource.objects.filter(pk=self.id).update(
            source_rdf=resource.serialize(format="nt"),
            source_updated=timezone.now(),
            stored=stored
        )
        return stored

    def get_named_graph(self):
        if not self.named_graph:
            self.named_graph = self._generate_namedgraph_uri()
        return self.named_graph

    @staticmethod
    def get_cache_url(uri):
        return get_cache_url(uri)

    @staticmethod
    def get_remote_lod_resource(url):
        return get_remote_lod_resource(url)

    @staticmethod
    def store_remote_cached_resource(graph, graph_store, named_graph):
        return store_remote_cached_resource(graph, graph_store, named_graph)

    def get_absolute_uri(self):
        return "/page/cache/{}".format(self.source_uri)


@receiver(post_save)
def create_rdf_lookup_links(sender, instance, **kw):
    if issubclass(instance.__class__, RDFModel):
        instance.update_linked_subjects()


@receiver(post_save, sender=CacheResource)
def update_in_index(sender, instance, **kw):
    from . import tasks
    chain(
        tasks.store_cache_resource.delay(instance),
        tasks.update_rdf_in_index.delay(instance)
    )


@receiver(post_delete, sender=CacheResource)
def remove_from_index(sender, instance, **kw):
    from . import tasks
    chain(
        tasks.remove_rdf_from_index.delay(instance),
        tasks.delete_rdf_resource.delay(instance)
    )

