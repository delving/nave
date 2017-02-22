# -*- coding: utf-8 -*-
"""This module test the RDFResolver."""
from nave.lod.utils.resolver import RDFRecord, NAVE, EDM

test_rdf = """
<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:edm="http://www.europeana.eu/schemas/edm/" xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:nave="http://schemas.delving.eu/nave/terms/" xmlns:ore="http://www.openarchives.org/ore/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:skos="http://www.w3.org/2004/02/skos/core#">
    <ore:Aggregation rdf:about="http://data.jck.nl/resource/aggregation/jhm-museum/M006660">
        <edm:aggregatedCHO rdf:resource="http://data.jck.nl/resource/document/jhm-museum/M006660"/>
        <edm:dataProvider>Joods Historisch Museum</edm:dataProvider>
        <edm:isShownAt rdf:resource="http://data.jck.nl/resource/aggregation/jhm-museum/M006660"/>
        <edm:isShownBy rdf:resource="http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d602/602N142.jpg&amp;width=2000"/>
        <edm:object rdf:resource="http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d602/602N142.jpg&amp;width=500"/>
        <edm:provider>Joods Historisch Museum</edm:provider>
        <edm:rights>http://creativecommons.org/publicdomain/mark/1.0/</edm:rights>
    </ore:Aggregation>
    <edm:ProvidedCHO rdf:about="http://data.jck.nl/resource/document/jhm-museum/M006660">
        <dc:creator rdf:resource="http://data.jck.nl/resource/skos/thespersoon/562"/>
        <dc:date>1963</dc:date>
        <dc:identifier>M006660</dc:identifier>
        <dc:rights>cop. Erven Antonie Witsel</dc:rights>
        <dc:source>Joods Historisch Museum. Aangekocht met steun van de Stichting Vrienden van het JHM</dc:source>
        <dc:title>Obbene sjoel</dc:title>
        <edm:type>IMAGE</edm:type>
    </edm:ProvidedCHO>
    <edm:WebResource rdf:about="urn:joods-historisch/d602/602N142.jpg">
        <nave:allowDeepZoom>true</nave:allowDeepZoom>
        <nave:allowSourceDownload>true</nave:allowSourceDownload>
        <nave:allowSourceDownload>false</nave:allowSourceDownload>
        <nave:allowPublicWebView>true</nave:allowPublicWebView>
    </edm:WebResource>
    <edm:WebResource rdf:about="urn:joods-historisch/d084/084B034.jpg">
        <nave:allowDeepZoom>true</nave:allowDeepZoom>
        <nave:allowSourceDownload>true</nave:allowSourceDownload>
        <nave:allowSourceDownload>false</nave:allowSourceDownload>
        <nave:allowPublicWebView>true</nave:allowPublicWebView>
    </edm:WebResource>
    <edm:WebResource rdf:about="urn:joods-historisch/d067/067B027.jpg">
        <nave:allowDeepZoom>true</nave:allowDeepZoom>
        <nave:allowSourceDownload>true</nave:allowSourceDownload>
        <nave:allowSourceDownload>false</nave:allowSourceDownload>
        <nave:allowPublicWebView>true</nave:allowPublicWebView>
    </edm:WebResource>
    <edm:Agent rdf:about="http://data.jck.nl/resource/skos/thespersoon/562">
        <skos:prefLabel>Witsel, Anton (1911-1977)</skos:prefLabel>
        <foaf:name>Witsel, Anton (1911-1977)</foaf:name>
    </edm:Agent>
    <skos:Concept rdf:about="http://data.jck.nl/resource/skos/thesau/90073892">
        <skos:prefLabel>synagoge</skos:prefLabel>
    </skos:Concept>
    <skos:Concept rdf:about="http://data.jck.nl/resource/skos/thesau/90001111">
        <skos:prefLabel>Obbene Sjoel</skos:prefLabel>
        <skos:note>Obbene Sjoel, bouwjaar: 1685</skos:note>
    </skos:Concept>
    <skos:Concept rdf:about="http://data.jck.nl/resource/skos/thesau/90182174">
        <skos:prefLabel>Amsterdam</skos:prefLabel>
    </skos:Concept>
    <skos:Concept rdf:about="http://data.jck.nl/resource/skos/thesau/90000842">
        <skos:prefLabel>synagogencomplex</skos:prefLabel>
    </skos:Concept>
    <nave:BrabantCloudResource>
        <nave:collection>Museum Collectie</nave:collection>
        <nave:collectionPart>Museumcollectie</nave:collectionPart>
        <nave:dimension>hoogte: 88.3 cm</nave:dimension>
        <nave:dimension>breedte: 67.5 cm</nave:dimension>
        <nave:formatted>signatuur (l.o., ):
Anton Witsel </nave:formatted>
        <nave:formatted>datering (l.o., ):
1963 </nave:formatted>
        <nave:formatted>opschrift (, ):
Documentatie - Nejen sjoel </nave:formatted>
        <nave:material>papier</nave:material>
        <nave:objectNumber>M006660</nave:objectNumber>
        <nave:objectSoort>vrije grafiek</nave:objectSoort>
        <nave:place>Nederland</nave:place>
        <nave:technique>grafiek</nave:technique>
        <nave:technique>lithografie</nave:technique>
        <nave:thumbLarge>http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d602/602N142.jpg&amp;width=2000</nave:thumbLarge>
        <nave:thumbLarge>http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d067/067B027.jpg&amp;width=2000</nave:thumbLarge>
        <nave:thumbLarge>http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d084/084B034.jpg&amp;width=2000</nave:thumbLarge>
        <nave:thumbSmall>http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d602/602N142.jpg&amp;width=500</nave:thumbSmall>
    </nave:BrabantCloudResource>
    <nave:DelvingResource>
        <nave:deepZoomUrl>http://prod.jck.hubs.delving.org/api/webresource/?spec=joods-historisch&amp;uri=urn:joods-historisch/d602/602N142.jpg&amp;docType=deepzoom</nave:deepZoomUrl>
        <nave:fullText>M006660, vrije grafiek, Anton Witsel, 1963</nave:fullText>
        <nave:featured>false</nave:featured>
        <nave:allowLinkedOpenData>true</nave:allowLinkedOpenData>
        <nave:public>true</nave:public>
    </nave:DelvingResource>
</rdf:RDF>
"""

def test__rdfrecord__resolve_webresource_uris():
    """Test if web resource uris are added."""
    from rdflib import Graph, URIRef
    g = Graph()
    g.parse(data=test_rdf, format="xml")
    assert g
    res, graph = RDFRecord.resolve_webresource_uris(
        graph=g,
        source_check=False
    )
    assert all(isinstance(r, URIRef) for r in res)
    assert len(list(res)) == 3
    assert graph
    derivative_list = [
        NAVE.thumbnailLarge,
        NAVE.thumbnailSmall,
        NAVE.deepZoomUrl
    ]
    for wr in res:
        predicates = list(graph.predicates(subject=wr))
        assert all(pred in predicates for pred in derivative_list)
    assert len(list(graph.objects(predicate=NAVE.thumbnailSmall))) == 3
    assert len(list(graph.objects(predicate=EDM.isShownBy))) == 3
    print(list(graph.objects(predicate=EDM.isShownBy)))
    assert all(
        x.startswith('http://') for x in list(
            graph.objects(predicate=NAVE.thumbnailSmall)
        )
    )
