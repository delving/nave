# -*- coding: utf-8 -*- 
import pytest
from rdflib import Graph, URIRef, Literal

from nave import lod
from nave.void.models import DataSet, ProxyResourceField

test_graph = """
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:nave="http://schemas.delving.eu/nave/terms/" xmlns:ore="http://www.openarchives.org/ore/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <ore:Aggregation rdf:about="http://acc.dcn.delving.org/resource/aggregation/afrikamuseum/100-1">
        <edm:aggregatedCHO rdf:resource="http://acc.dcn.delving.org/resource/document/afrikamuseum/100-1"/>
        <edm:dataProvider>Nationaal Museum van Wereldculturen</edm:dataProvider>
        <edm:isShownAt rdf:resource="http://afrikamuseum.cithosting.nl/deeplink.asp?o=100-1"/>
        <edm:isShownBy rdf:resource="http://afrikamuseum.cithosting.nl/imageproxy.asp?server=62.221.199.184&amp;port=12842&amp;filename=afrika/screen/100-1.jpg"/>
        <edm:object rdf:resource="http://afrikamuseum.cithosting.nl/imageproxy.asp?server=62.221.199.184&amp;port=12842&amp;filename=afrika/screen/100-1.jpg"/>
        <edm:provider>Rijksdienst voor het Cultureelerfgoed</edm:provider>
        <edm:rights>http://creativecommons.org/publicdomain/zero/1.0/</edm:rights>
    </ore:Aggregation>
    <edm:ProvidedCHO rdf:about="http://acc.dcn.delving.org/resource/document/afrikamuseum/100-1">
        <dc:coverage>Bangassou</dc:coverage>
        <dc:coverage>Zande</dc:coverage>
        <dc:description>Antropomorf figuur van donker hout. In het hoofd zijn de ogen diep uitgehold, vanaf de ogen lopen groeven naar achteren zodoende het haar voorstellende. De armen zitten in een bijna gesloten ruitvorm voor het lichaam. Ze zijn grof uitgebeiteld. Het figuur heeft korte beentjes en kleine voetjes. De rug loopt een beetje rond, hieronder twee kettinkjes, één van ronde, rode kraaltjes en één van langwerpige, voor het merendeel gele en enkele blauwe kraaltjes en een rode, zwarte en groene kraal.</dc:description>
        <dc:description>Dit beeld is verbonden met met geheime Mani- of Yanda-genootschap. Deze groepering stond open voor mannen en vrouwen en was sterk hiërarchisch van opbouw. Als voornaamste doel had het genootschap de oganisatie van groepsrituelen en de onthulling van geheime 'medicijnen' die de groepsleden bescherming, vruchtbaarheid en succes moesten bieden. Er vonden ook feesten plaats, soms met maskers, en er werd rechtspraak uitgeoefend voor het oplossen van conflicten tussen leden. Uniek en typisch voor het Mani genootschap was het gebruik van kleine beelden vervaardigd uit hout of leem, de zogeheten yanda's. De term yanda dekt vele ladingen: naast de beeldjes zelf duidt hij elk ritueel voorwerp van het genootschap aan, alsook de geest of kracht die de leden bijstaat, of het genootschap in zijn geheel. De yanda's dienden voor persoonlijk gebruik. Er werd op hen beroep gedaan voor een goede jacht of oogst, tegen onvruchtbaarheid of een ongunstige rechtspraak, om de huiselijke vrede te bevorderen en om bescherming te bekomen tegen ziekte of beheksing. Zij werden als orakel geconsulteerd en aangezocht om beheksers te straffen. Om een beeld krachtig te maken en gunstig te stemmen moest de eigenaar het geregeld inwrijven met roodhoutpoeder en met magische mani-spijs. De yanda's werden getooid met kralensnoeren, muntstukken, koperen ringetjes of armbanden en hadden verder recht op een deel van de oogst, jachtbuit of winst waartoe ze hadden bijgedragen. Dit beeldje diende als vruchtbaarheidsbeeldje om een meisje te krijgen. Het wordt tussen de slapende gelegd.</dc:description>
        <dc:format>H 16 cm x B 5,5 cm x Dp 5,5 cm</dc:format>
        <dc:identifier>Inventarisnummer_100-1</dc:identifier>
        <dc:relation>Cf. collectienummer 100-2</dc:relation>
        <dc:rights>Afrika Museum, Berg en Dal</dc:rights>
        <dc:subject>beelden</dc:subject>
        <dc:subject>hulpmiddelen bij ritueel etc.</dc:subject>
        <dc:subject>representaties van het bovenaardse</dc:subject>
        <dc:subject>hulpmiddelen bij ritueel etc.</dc:subject>
        <dc:subject>representaties van het bovenaardse</dc:subject>
        <dc:title>YandaKorte Omschrijving</dc:title>
        <dc:title>Beeld</dc:title>
        <dcterms:spatial>Bangassou</dcterms:spatial>
        <dcterms:spatial>Zande</dcterms:spatial>
        <edm:type>IMAGE</edm:type>
    </edm:ProvidedCHO>
    <edm:WebResource rdf:about="http://afrikamuseum.cithosting.nl/imageproxy.asp?server=62.221.199.184&amp;port=12842&amp;filename=afrika/screen/100-1.jpg"/>
    <nave:DcnResource>
        <nave:location>Berg en Dal</nave:location>
        <nave:province>Gelderland</nave:province>
    </nave:DcnResource>
</rdf:RDF>
"""


ds_fields = {'data_owner': 'Nationaal Museum van Wereldculturen',
             'dataset_type': 1,
             'description': '',
             'document_uri': 'http://acc.dcn.delving.org/resource/dataset/afrikamuseum',
             'file_watch_directory': '',
             'invalid': 0,
             'name': 'Afrika Museum',
             'named_graph': 'http://acc.dcn.delving.org/resource/dataset/afrikamuseum/graph',
             'oai_pmh': 2,
             'process_key': '',
             'processed_records': 4200,
             'published': True,
             'records_in_sync': False,
             'skos_in_sync': False,
             'spec': 'afrikamuseum',
             'stay_in_sync': True,
             'total_records': 7939,
             'user': None,
             'valid': 7939}


@pytest.mark.django_db
def test__proxyresourcefield__save_with_only_property():
    sample_url = "http://purl.org/dc/elements/1.1/title"
    ds = DataSet.objects.create(**ds_fields)
    field = ProxyResourceField(property_uri=sample_url, dataset_uri=ds.document_uri)
    assert field
    assert field.property_uri == sample_url
    assert field.dataset_uri == ds.document_uri
    assert not field.search_label
    assert not field.dataset
    field.save()
    field = ProxyResourceField.objects.get(id=field.pk)
    assert field.search_label
    assert field.search_label == "dc_title"
    assert field.dataset
    assert field.dataset == ds


# @pytest.mark.django_db
# def test__proxyresourcefield__save_with_search_label():
#     sample_url = "http://purl.org/dc/elements/1.1/title"
#     field = ProxyResourceField(
#         property_uri=sample_url,
#         search_label="dc_title2"
#     )
#     assert field.search_label == "dc_title2"
#     field.save()
#     field = ProxyResourceField.objects.get(id=field.pk)
#     assert field.search_label == "dc_title2"
#
#
# @pytest.mark.django_db
# def test__proxyresourcefield__no_duplicates_allowed():
#     sample_url = "http://purl.org/dc/elements/1.1/title"
#     assert ProxyResourceField.objects.count() == 0
#     field = ProxyResourceField(
#         property_uri=sample_url,
#         search_label="dc_title"
#     )
#     field.save()
#     assert ProxyResourceField.objects.count() == 1
#     with pytest.raises(IntegrityError):
#         field = ProxyResourceField.objects.create(property_uri=sample_url)
#         assert ProxyResourceField.objects.count() == 1
#
#
# @pytest.mark.django_db
# def test__dataset__exclusion_fields():
#     ds = DataSet.objects.create(**ds_fields)
#     assert ds is not None
#     assert not ds.excluded_index_fields.names()
#     ds.excluded_index_fields.add("dc_rights")
#     ds.save()
#     ds = DataSet.objects.get(id=ds.id)
#     assert 'dc_rights' in ds.excluded_index_fields.names()


# @pytest.mark.django_db
# def test__dataset__property_resource_fields():
#     sample_url = "http://purl.org/dc/elements/1.1/title"
#     ds = DataSet.objects.create(**ds_fields)
#     assert ds is not None
#     assert ds.proxy_fields.count() == 0
#     proxy_field = ProxyResourceField.objects.create(property_uri=sample_url)
#     ds.proxy_fields.add(proxy_field)
#     assert ds.proxy_fields.count() == 1
#     ds.proxy_fields.add(proxy_field)
#     assert ds.proxy_fields.count() == 1


@pytest.mark.django_db
def test__dataset__add_proxy_resource_uris_to_graph():
    sample_url = "http://purl.org/dc/elements/1.1/subject"
    ds = DataSet.objects.create(**ds_fields)
    assert ds

    proxy_field = ds.generate_proxyfield_uri("Sjoerd, Siebinga", language="nl")
    assert proxy_field.endswith("/resource/dataset/afrikamuseum/nl/Sjoerd,_Siebinga")
    proxy_field = ds.generate_proxyfield_uri("Sjoerd, Siebinga", language=None)
    assert proxy_field.endswith("/resource/dataset/afrikamuseum/Sjoerd,_Siebinga")

    graph = Graph(identifier="http://acc.dcn.delving.org/resource/aggregation/afrikamuseum/100-1")
    graph.namespace_manager = lod.namespace_manager
    graph.parse(data=test_graph, format='xml')
    assert graph
    assert len(list(graph.objects(predicate=URIRef(sample_url)))) == 3
    assert all(isinstance(obj, Literal) for obj in graph.objects(predicate=URIRef(sample_url)))

    new_graph, converted_literals = ds.update_graph_with_proxy_field(graph, sample_url)
    assert new_graph
    assert converted_literals
    assert all(isinstance(obj, URIRef) for obj in new_graph.objects(predicate=URIRef(sample_url)))

    assert len(converted_literals) == 3
    coined_uri, obj = sorted(converted_literals)[0]
    assert coined_uri.endswith('/resource/dataset/afrikamuseum/beelden')
    assert obj.value == 'beelden'

