jQuery(document).ready(function ($) {
    jQuery(document).delvingInstant({
        configHelp: false,
        usePushState: true,
        endPoint: "https://data.collectienederland.nl",
        //endPointPath: "",
        // endPointPath: "/vc/zuiderzeemuseum-modemuze/api/",
        orgId: "dcn",
        collectionSpecs: [
            "zuiderzeemuseum", 
            "noord-hollands-archief"
        	],
        dataOwner: "",
        defaultImg: "images/placeholder.svg",
        language: "nl",
        rows: 16,
        resultsGridClasses: "col-xl-3 col-lg-4 col-md-6 col-sm-6 col-12",
        resultsLayout: "grid",
        resultsLayoutToggle: true,
        searchOnPageInit: true,
        downloadImage: true,
        pageId:"page",
        pageNrParameter:"pg",
        feedbackUserKey: "",
        feedbackObjectField: "dc_identifier",
        label: {
            collapse: "Minder [-]",
            expand: "Meer [+]",
            viewInOriginalContext: "Bekijk in oorspronkelijke context",
            goTo: "Ga naar: ",
            next: "Volgende",
            noResults: "Geen resultaten gevonden",
            previous: "Vorige",
            numberOfResults: "Gevonden: ",
            downloadImage: "Afbeelding downloaden",
            returnToSearchResults: "Terug naar resultaten",
            search: "Zoeken",
            searchResults: "Zoekresultaten",
            advancedSearch: "Geavanceerd zoeken",
            advancedSearchClose: "Geavanceerd zoeken sluiten",            
            boolAnd: "EN",
            boolNot: "NIET",
            boolOr: "OF",
            searchInputPlaceholder: "",
            relatedItems: "Soortgelijke inhoud",
            sort: "Sorteer",
            sortAlphabetic: "Naam",
            sortNumeric: "Resultaten",
            feedbackFormToggle: "Feedback over dit object",
            feedbackFormSubmit: "Verstuur",
            feedbackFormUserName: "Uw naam",
            feedbackFormUserEmail: "Uw e-mailadres",
            feedbackText: "Feedback",
            feedbackError: "Er is iets fout gegaan met het verzenden van uw feedback. Neem contact op met de beheerder van deze website.",
            feedbackSuccess: "Uw feedback is verzonden."
        },
        layout: {
            simpleSearchBlock: "#diw-search",
            advancedSearchBlock: "#diw-advanced-search",
            queryInfoBlock: "#diw-query-info",
            breadcrumbsBlock: "#diw-breadcrumbs",
            paginationBlock: ".diw-pagination",
            resultsBlock: "#diw-results",
            facetsBlock: "#diw-facets",
            itemMediaBlock: "#diw-item-media",
            itemDataBlock: "#diw-item-data",
            itemRelatedBlock: "#diw-item-related"
        },
        useAdvancedSearch: true,
        advancedSearchFields: [
            {name: "", label: "Alle velden"},
            {name: "dc_date_text", label: "Datum"},
            {name: "dc_title_text", label: "Titel"},
            {name: "icn_material_text", label: "Materiaal"},
            {name: "dc_subject_text", label: "Onderwerp"}
        ],
        showOriginalContextLink: false,
        orignalContextField: "europeana_isShownAt",
        textExpander: true,
        maxCharactersResults: "500",
        maxCharactersItem: "1000",
        maxCharactersTitle: "100",
        thumbnailWidth: "100%",
        resizeResultThumbnails: true,
        resizeRelatedItemsThumbnails: true,
        useDeepZoom: true,
        deepZoomControlImages: "images/seadragon/",
        deepZoomSequenceButtons: true,
        deepZoomImageNavigator: false,
        deepZoomRotationControl: true,
        thumbnailField: "delving_thumbnail",
        displayFacets: [
            {name:"europeana_dataProvider_facet", label:"Collectie"},
            {name:"dc_subject_facet", label:"Onderwerp"},
            {name:"dc_type_facet", label:"Soort object"},
            {name:"icn_material_facet", label:"Materiaal"},
            {name:"icn_technique_facet", label:"Techniek"},
            {name:"dc_creator_facet", label:"Vervaardiger"}
        ],
        customFacets: [],
        collapseFacets: false,
        sortFacets: true,
        sortFacetsAlphaDefault: false,
        explodeFacets: false,
        resultFields: [
            {name:"dc_title", label:""},
            {name:"dc_date", label:""},
            {name:"europeana_dataProvider", label:"Bron"},
        ],
        itemFields: [
            {id:"identificatie", label:"Identificatie", fields:[                
                {name:"dc_title",label:"Titel"},
                {name:"dcterms_alternative",label:"Alternatief"},
                {name:"dc_description",label:"Omschrijving"},
                {name:"dc_identifier",label:"Objectnummer"},
                {name:"dc_type",label:"Soort object", newQuery:true},
                {name:"nave_inscription",label:"Inscriptie"},
            ]},
            {id:"vervaardiging", label:"Vervaardiging", fields:[
                {name:"nave_creatorRole",label:"Vervaardiger rol"},
                {name:"dc_creator",label:"Vervaardiger", newFacetQuery:true},                
                {name:"dc_contributor",label:"Bijdrager", newQuery:true},
                {name:"dc_date",label:"Datum vervaardiging"},
                {name:"dcterms_issued",label:"Datum uitgave"},
                {name:"dc_coverage",label:"Vervaardigingsplaats / vindplaats", newQuery:true},
            ]},
            {id:"fysieke_kenmerken", label:"Fysieke kenmerken", fields:[
                {name:"dcterms_medium",label:"Medium", newQuery:true},
                {name:"icn_material",label:"Materiaal", newFacetQuery:true},                
                {name:"icn_technique",label:"Techniek", newQuery:true},
                {name:"dc_format",label:"Formaat"},
            ]},
            {id:"bron", label:"Bron", fields:[
                {name:"edm_isShownAt",label:"Originele context" },
                {name:"dc_source",label:"Bron"},                
                {name:"edm_dataProvider",label:"Dataprovider"},
                {name:"dc_publisher",label:"Uitgever"},
                {name:"dcterms_provenance",label:"Herkomst", newFacetQuery: true}
            ]},
            {id:"onderwerp", label:"Onderwerp", fields:[
                {name:"dc_subject",label:"Onderwep", newQuery: true },
                {name:"dcterms_spatial",label:"Waar"},                
                {name:"dcterms_temporal",label:"Wanneer"},
            ]},
            {id:"rechten", label:"Rechten en licenties", fields:[
                {name:"dc_rights", label:"Rechthebbende", linkText:"", externalLink: true},
                {name:"europeana_rights", label:"Gebruiksrecht", linkText:"", externalLink: true}
            ]},
            {id:"documentatie", label:"Documentatie", fields:[
                {name:"dcterms_isReferencedBy", label:"Is verwezen door"},
                {name:"dcterms_references", label:"Verwijst naar"}
            ]},
            {id:"documentatie", label:"Documentatie", fields:[
                {name:"nave_collectionPart", label:"Deelcollectie"},
                {name:"dc_relation", label:"Verwijst naar"},
                {name:"edm_isRelatedTo", label:"Is gerelateerd aan"},
                {name:"dcterms_isPartOf", label:"Is deel van"},
                {name:"dcterms_hasPart", label:"Heeft deel"},
                {name:"dcterms_hasVersion", label:"Heeft versie"},
                {name:"dcterms_isVersionOf", label:"Is een versie van"},
                {name:"dcterms_replaces", label:"Vervangt"},
                {name:"dcterms_isReplacedBy", label:"Is vervangen door"},
                {name:"dcterms_requires", label:"Vereist"},
                {name:"dcterms_isRequiredBy", label:"Is vereist door"},
                {name:"edm_incorporates", label:"Omvat"},
                {name:"edm_isDerivativeOf", label:"Is afgeleid van"},
                {name:"edm_isRepresentationOf", label:"Is een weergave van"}
            ]},           
        ],
        itemImageFields: {thumb: "icn_thumbLarge", image: "icn_thumbLarge", imageAlt: "europeana_isShownBy", deepZoomUrl: "delving_deepZoomUrl"},
        relatedItemsFields: [
            {name:"dc_title",label:"Titel"},
        ],
        showRelatedItems: true,
        relatedItemsCount: 4,
        relatedItemsGridClasses: "col-lg-3 col-md-3 col-sm-6 col-xs-12"
    });

});