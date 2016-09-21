# -*- coding: utf-8 -*-
"""

"""
from unittest import TestCase
import pytest

from nave.lod.utils.rdfstore import RDFStore, UnknownGraph


class TestRDFSTore(TestCase):
    """
    Test class for the functions in the RDFStore class
    """
    store = RDFStore(db="test", host="http://localhost", port=3030)
    acceptances_store = RDFStore(db="test", host="http://localhost", port=3030, acceptance_mode=True)
    graph_store = store.get_graph_store
    n3_string = """
           <http://localhost:8000/resource/organisation/ton_smits_huis> <http://purl.org/dc/terms/subject> <dbpedia-nl:Ton_Smits> .
    <http://localhost:8000/resource/organisation/ton_smits_huis> <http://www.w3.org/2000/01/rdf-schema#label> "Ton Smits Huis" .
    <http://localhost:8000/resource/organisation/ton_smits_huis> <http://xmlns.com/foaf/0.1/homepage> <http://tonsmitshuis.nl/> .
    <http://localhost:8000/resource/organisation/ton_smits_huis> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://xmlns.com/foaf/0.1/Organisation> .
    <http://localhost:8000/resource/organisation/tsh> <http://www.w3.org/2002/07/owl#sameAs> <http://localhost:8000/resource/organisation/ton_smits_huis> .
        """
    cached_n3 = """
                <http://nl.dbpedia.org/resource/Ton_Smits> <http://www.w3.org/2002/07/owl#sameAs> <http://nl.dbpedia.org/resource/Ton_Smits> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageEditLink> <http://nl.wikipedia.org/w/index.php?title=Ton_Smits&action=edit> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageLength> "3300"^^<http://www.w3.org/2001/XMLSchema#integer> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://www.w3.org/2000/01/rdf-schema#comment> "Antonie Gerardus (Ton) Smits (Veghel, 18 februari 1921 \\u2013 Eindhoven, 5 augustus 1981) was een Nederlands cartoonist en striptekenaar. Hij wordt wel gezien als de eerste Nederlandse cartoonist die internationale bekendheid verwierf.Hij is geboren te Veghel in 1921. In 1938 verhuisde hij naar Eindhoven. Van 1939 tot 1944 studeerde hij aan de Academie voor Kunst en Vormgeving te \'s-Hertogenbosch."@nl .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageModified> "2011-12-17T10:58:12+00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://www.w3.org/2000/01/rdf-schema#label> "Ton Smits"@nl .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageExtracted> "2015-01-16T15:35:14+00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageRevisionID> "28683102"^^<http://www.w3.org/2001/XMLSchema#integer> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://purl.org/dc/terms/subject> <http://nl.dbpedia.org/resource/Categorie:Nederlands_cartoonist> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageOutDegree> "48"^^<http://www.w3.org/2001/XMLSchema#integer> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageRevisionLink> <http://nl.wikipedia.org/w/index.php?title=Ton_Smits&oldid=28683102> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://purl.org/dc/terms/subject> <http://nl.dbpedia.org/resource/Categorie:Nederlands_stripauteur> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageExtracted> "2014-11-17T15:16:54+00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageHistoryLink> <http://nl.wikipedia.org/w/index.php?title=Ton_Smits&action=history> .
<http://nl.dbpedia.org/resource/Smits> <http://dbpedia.org/ontology/wikiPageDisambiguates> <http://nl.dbpedia.org/resource/Ton_Smits> .
<http://nl.dbpedia.org/resource/Tom_Smits> <http://dbpedia.org/ontology/wikiPageRedirects> <http://nl.dbpedia.org/resource/Ton_Smits> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageExternalLink> <http://www.tonsmitshuis.nl/> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/wikiPageID> "82483"^^<http://www.w3.org/2001/XMLSchema#integer> .
<http://nl.wikipedia.org/wiki/Ton_Smits> <http://xmlns.com/foaf/0.1/primaryTopic> <http://nl.dbpedia.org/resource/Ton_Smits> .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://dbpedia.org/ontology/abstract> "Antonie Gerardus (Ton) Smits (Veghel, 18 februari 1921 \\u2013 Eindhoven, 5 augustus 1981) was een Nederlands cartoonist en striptekenaar. Hij wordt wel gezien als de eerste Nederlandse cartoonist die internationale bekendheid verwierf.Hij is geboren te Veghel in 1921. In 1938 verhuisde hij naar Eindhoven. Van 1939 tot 1944 studeerde hij aan de Academie voor Kunst en Vormgeving te \'s-Hertogenbosch. In 1941 publiceerde hij zijn eerste cartoon in het tijdschrift \'De Humorist\', toen nog onder het pseudoniem Tommy. Ook tekende hij spotprenten van nazi-kopstukken, die echter pas na de Tweede Wereldoorlog konden worden gepubliceerd in de vorm van prentbriefkaarten.In de Helmondse Courant publiceerde hij sinds 1946 de strips Karel Kwiek, Daniel Daazer en Dolly en de juwelenroof.In 1947 verhuisde Ton Smits naar Amsterdam. Hij tekende vele politieke prenten voor diverse Nederlandse dagbladen, zoals Het Vrije Volk en De Telegraaf. Nadat de dagbladen deze contracten abrupt hadden opgezegd, probeerde hij zijn tekeningen in de Verenigde Staten te verkopen, hetgeen aanvankelijk slechts moeizaam lukte.Mede dankzij de hulp van een Amerikaans agentschap kreeg hij in 1954 een contract bij The New Yorker aangeboden. Na een kort bezoek aan Amerika in 1955-1956 brak hij door in dit land. Van zijn verdiende geld liet hij door de architect Fons Vermeulen van de Bossche School een atelierwoning bouwen te Eindhoven, waar hij in 1957, samen met zijn moeder, ging wonen. Hier zou hij ook de schilderkunst weer gaan beoefenen, een oude liefhebberij van de kunstenaar.In 1964 won hij, met de cartoonstrip \'het kuikentje\', de Gouden Palm, wat de hoogst mogelijke onderscheiding is voor een cartoonist.Niet lang daarna volgden een aantal tegenslagen elkaar op: achteruitgang van de tijdschriftenmarkt in de Verenigde Staten, de dood van zijn agent in Amerika, de dood van zijn moeder, en een zware operatie. Doch hij kwam er bovenop en vond zelfs eindelijk een geliefde, Lidwien Zoetmulder, met wie hij in 1971 trouwde.Geleidelijk aan ging hij weer in Nederlandse bladen publiceren, terwijl hij van 1979 af aan zeer intensief met de schilderkunst bezig was. Hij maakte dromerige, maar vrolijke, schilderijen die tot de na\\u00EFeve kunst kunnen worden gerekend. In 1981 vond te Eindhoven een grote overzichtstentoonstelling van zijn werk plaats. Enkele maanden later overleed hij aan keelkanker. In zijn testament nam hij op dat een deel van zijn collectie voor de gemeenschap bewaard zou blijven, voor welk doel de \'Stichting Ton Smits\' werd opgericht.Dankzij deze inspanningen werd het Ton Smitshuis in 1983 voor het publiek geopend. Het bevindt zich in de Genneper Parken te Eindhoven.Er is een jaarlijkse cartoonprijs, de Ton Smits-penning, naar Smits vernoemd."@nl .
<http://nl.dbpedia.org/resource/Ton_Smits> <http://xmlns.com/foaf/0.1/isPrimaryTopicOf> <http://nl.wikipedia.org/wiki/Ton_Smits> .
    """
    test_named_graph = "http://localhost:8000/resource/graph/test"
    empty_named_graph = "http://localhost:8000/resource/graph/empty"

    def setup_method(self, method):
        """ Create the sample data
        """
        self.store._clear_all()
        self.store.graph_store.post(data=self.n3_string, named_graph=self.test_named_graph)
        self.store.graph_store.post(data="", named_graph=self.empty_named_graph)

    def teardown_method(self, method):
        """ teardown any state that was previously setup with a call to
        setup_method.
        """
        # self.store._clear_all()

    def test_acceptance_mode(self):
        assert self.acceptances_store.base_url.endswith("test_acceptance")

    def test_rdf_store_urls(self):
        assert self.store.get_graph_store_url.endswith("test/data")
        assert self.store.get_sparql_query_url.endswith("test/sparql")
        assert self.store.get_sparql_update_url.endswith("test/update")

    def test_ask_query(self):
        assert self.store.ask()
        assert not self.store.ask(named_graph=self.empty_named_graph)

    def test_count_query(self):
        assert self.store.count() == 5
        assert self.store.count(named_graph=self.test_named_graph) == 5
        assert self.store.count(named_graph=self.empty_named_graph) == 0

    def test_describe_query(self):
        graph = self.store.describe(
            uri="http://localhost:8000/resource/organisation/ton_smits_huis",
            named_graph=None
        )
        assert graph
        subjects = list(graph.subjects())
        assert len(subjects) == 4
        assert len(set(subjects)) == 1

    def test_empty_describe_query(self):
        graph = self.store.describe(
            uri="http://localhost:8000/resource/missing",
            named_graph=None
        )
        assert not graph

    # def test_remove_insert_query(self):
    # assert not self.store.ask(
    #         query="""where {<http://localhost:8000/resource/organisation/ton_smits_huis>
    #                <http://xmlns.com/foaf/0.1/homepage> <http://www.tonsmitshuis.nl/>}"""
    #     )
    #     response = self.store.remove_insert(
    #         remove="""<http://localhost:8000/resource/organisation/ton_smits_huis>
    #                <http://xmlns.com/foaf/0.1/homepage> <http://tonsmitshuis.nl/> .""",
    #         insert="""<http://localhost:8000/resource/organisation/ton_smits_huis>
    #                <http://xmlns.com/foaf/0.1/homepage> <http://www.tonsmitshuis.nl/> .""",
    #         named_graph=self.test_named_graph
    #     )
    #     assert response
    #     assert self.store.ask(
    #         query="""where {<http://localhost:8000/resource/organisation/ton_smits_huis>
    #                <http://xmlns.com/foaf/0.1/homepage> <http://www.tonsmitshuis.nl/>}"""
    #     )

    def test_clear_all(self):
        self.store._clear_all()
        assert not self.store.ask()

    def test_graph_store_post(self):
        self.store._clear_all()
        assert not self.store.ask()
        response = self.store.get_graph_store.post(data=self.n3_string, named_graph=self.test_named_graph)
        assert response
        assert self.store.ask()

    def test_graph_store_get(self):
        graph = self.store.get_graph_store.get(self.test_named_graph, as_graph=True)
        assert "http://localhost:8000/resource/organisation/ton_smits_huis" in [subj.toPython() for subj in
                                                                                graph.subjects()]
        with pytest.raises(UnknownGraph):
            graph = self.store.get_graph_store.get("http://missing_graph", as_graph=True)

    def test_graph_store_head(self):
        assert self.store.get_graph_store.head(self.test_named_graph)
        assert not self.store.get_graph_store.head("http://missing_graph")

    def test_graph_store_delete(self):
        assert self.store.get_graph_store.head(self.test_named_graph)
        self.store.get_graph_store.delete(self.test_named_graph)
        assert not self.store.get_graph_store.head(self.test_named_graph)

    def test_get_all_triples_from_graph(self):
        response = self.store.select("""
            ?s ?p ?o ?g {
                {GRAPH ?g {<http://localhost:8000/resource/organisation/ton_smits_huis> ?p2 ?o2}}
               UNION
               {GRAPH ?g {?s ?p ?o}}
            }
        """)
        assert response


        # def test_cache_graph(self):
        #     cache_graph = "http://localhost:8000/resource/graph/cached"
        #     response = self.store.get_graph_store.post(data=self.cached_n3, named_graph=cache_graph)
        #     assert response
        #     assert self.store.ask(named_graph=cache_graph)
