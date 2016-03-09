from django.conf import settings

from rdflib import Literal, URIRef, ConjunctiveGraph

from void.models import EDMRecord, DataSet

from lod.utils.rdfstore import get_rdfstore


class EDMBulkLoader:
    """
    Load EDM records processed by Narthex directly into Nave.
    """

    def __init__(self, spec, path, base_url=settings.RDF_BASE_URL):
        self.spec = spec
        self.path = path

    @staticmethod
    def add_triples(graph, subject, value_dict):
        for k, v in value_dict.items():
            obj = Literal(v)
            if v.startswith("http:"):
                obj = URIRef(v)
            graph.add( (subject, URIRef(k), obj) )
        return graph

    def create_actor_subject_uri(self, actor_name, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        return URIRef("{}/resource/actor/{}".format(base_url.rstrip('/'), actor_name))

    def create_actor(self, actor_name, base_url=None, named_graph="http://schemas.delving.eu/narthex/terms/Actors/graph"):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        g = ConjunctiveGraph(identifier=URIRef(named_graph))
        subject = self.create_actor_subject_uri(actor_name)
        values = {
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://schemas.delving.eu/narthex/terms/Actor",
            "http://schemas.delving.eu/narthex/terms/username": actor_name,
            "http://schemas.delving.eu/narthex/terms/passwordHash": "c66ed5e2e6a32fa384176805f380bd77924f2c76aff2a2dcb6429367a14d1e74",
        }
        self.add_triples(g, subject, values)
        return g

    def create_dataset_subject_uri(self, spec, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        return URIRef("{}/resource/dataset/{}".format(base_url, spec))

    def create_dataset(self, spec, actor, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        subject = self.create_actor_subject_uri(spec, base_url=base_url)
        named_graph = subject + "/graph"
        actor_subject = self.create_actor_subject_uri(actor, base_url=base_url)
        g = ConjunctiveGraph(identifier=named_graph)
        values = {
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "http://schemas.delving.eu/narthex/terms/Dataset",
            "http://schemas.delving.eu/narthex/terms/acceptanceMode": "false",
            "http://schemas.delving.eu/narthex/terms/acceptanceOnly": "true",
            "http://schemas.delving.eu/narthex/terms/actorOwner": str(actor_subject),
            "http://schemas.delving.eu/narthex/terms/datasetCharacter": "character-mapped",
            "http://schemas.delving.eu/narthex/terms/datasetMapToPrefix": "edm",
            "http://schemas.delving.eu/narthex/terms/datasetSpec": spec,
            "http://schemas.delving.eu/narthex/terms/publishIndex": "true",
            "http://schemas.delving.eu/narthex/terms/publishLOD": "true",
            "http://schemas.delving.eu/narthex/terms/publishOAIPMH": "true",
            "http://schemas.delving.eu/narthex/terms/synced": "false",
            "http://schemas.delving.eu/narthex/terms/datasetName": spec,
            "http://schemas.delving.eu/narthex/terms/datasetDescription": spec,
            "http://schemas.delving.eu/narthex/terms/datasetAggregator": "{} Aggregator".format(spec),
            "http://schemas.delving.eu/narthex/terms/datasetOwner": "{} Owner".format(spec),
            "http://schemas.delving.eu/narthex/terms/datasetLanguage": "NL",
            "http://schemas.delving.eu/narthex/terms/datasetRights": "http://creativecommons.org/publicdomain/mark/1.0/",
        }
        self.add_triples(g, subject, values)
        return g

    def store_ds(self, spec, actor, base_url=None):
        # TODO fix this so new datasets can be created this way
        if not base_url:
            base_url = settings.RDF_BASE_URL
        store = get_rdfstore().get_graph_store
        actor_graph = self.create_actor(actor_name=actor)
        result = store.post(str(actor_graph.identifier), data=actor_graph)
        if not result:
            raise Exception()
        dataset_graph = self.create_dataset(spec, actor, base_url)
        result = store.put(str(dataset_graph.identifier), data=dataset_graph)
        if not result:
            raise Exception()

    def parse_narthex_xml(self, actor, base_url=None):
        if not base_url:
            base_url = settings.RDF_BASE_URL
        ds = DataSet.objects.filter(spec=self.spec)
        graph_name = self.create_dataset_subject_uri(self.spec, base_url) + "/graph"
        if not ds:
            self.store_ds(self.spec, actor, base_url)
            ds = DataSet.get_dataset_from_graph(dataset_graph_uri=str(graph_name))
        else:
            ds = ds.first()
        return ds.process_narthex_file(path=self.path, console=True)


