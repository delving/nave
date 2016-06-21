jQuery(document).ready(function($) {
    jQuery(document).delvingInstant({
        configHelp: true,
        endPoint: "",
        orgId: "",
        dataProviders: [],
        collectionSpecs: [],
        dataOwner: "",
        rows: 12,
        resultsLayout: "list",
        defaultImg: "images/blank.png",
        language: "nl",  
        label:{
            collapse: "Minder&nbsp;[-]",
            expand: "Meer&nbsp;[+]",
            viewInOriginalContext: "Bekijk in oorspronkelijke context",
            goTo: "Ga naar: ",
            next: "Volgende",
            noResults: "Geen resultaten gevonden",
            previous: "Vorige",
            numberOfResults: "Gevonden: ",
            returnToSearchResults: "Terug naar resultaten",
            search: "Zoeken",
            searchResults: "Zoekresultaten",
            advancedSearch: "Geavanceerd zoeken",
            advancedSearchClose: "Geavanceerd zoeken sluiten",
            boolAnd: "EN",
            boolNot: "NIET",
            boolOr: "OF",
            relatedItems: "Soortgelijke inhoud",
            sort: "Sorteer"
        },
        layout: {
            simpleSearchBlock: "#diw-search",
            //advancedSearchBlock: "#diw-advanced-search",
            queryInfoBlock: "#diw-query-info",
            paginationBlock: ".diw-pagination",
            resultsBlock: "#diw-results",
            facetsBlock: "#diw-facets",
            itemMediaBlock: "#diw-item-media",
            itemDataBlock: "#diw-item-data",
        },
        linkToExternalLandingPage: false,
        textExpander: true,
        maxCharactersResults: "255",
        maxCharactersItem: "1000",
        maxCharactersTitle: 200,
        thumbnailWidth:"244",
        useDeepZoom: true,
        useFlashZoom: true,
        deepZoomFlashFile: "flash/OpenZoomViewer.swf",
        deepZoomControlImages: "images/seadragon/",
        resultFields: [
            {name:"dc_title"},
            {name:"dc_creator",label:"Vervaardiger"},
            {name:"dc_date",label:"Datum"},
            {name:"dc_description",label:"Beschrijving"}
        ],
        collapseFacets: false,
        customFacets: [],
        sortFacets: true,
        displayFacets: [      
            {name:"delving_provider_facet", label:"Provider"},
            {name:"delving_owner_facet", label:"Data owner"},
            {name:"tib_material_facet",label:"Materiaal"},
            {name:"dc_type_facet", label:"Object type"}
            
        ],
        thumbnailField: "delving_thumbnail",
        itemFields: [
            {name:"dc_title",label:"Titel"},
            {name:"dc_description",label:"Beschrijving"},
            {name:"dc_creator",label:"Vervaardiger"},
            {name:"dcterms_created",label:"Vervaardigingsdatum"},
            {name:"dc_subject",label:"Onderwerp"},
            {name:"dc_type", label: "Materiaal"},
            {name:"dcterms_medium",label:"Medium"},
            {name:"tib_objectSoort",label:"Soort object"},
            {name:"tib_dimension",label:"Afmetingen"},
            {name:"europeana_country",label:"Land"},
            {name:"europeana_language",label:"Taal"},
            {name:"europeana_rights",label:"Rechten"},
            {name:"europeana_collectionName",label:"Collectie"},
            {name:"dc_source",label:"Source"}
            
        ],
        itemImageFields: {
            thumb:"delving_thumbnail",
            image:"tib_thumbLarge",
            imageAlt:"europeana_object",
            deepZoomUrl:"delving_deepZoomUrl"
        },
        relatedItemsFields: {
            thumb:"delving_thumbnail",
            title:"dc_title"
        },
        showRelatedItems: true,
        relatedItemsCount: 5,
        relatedItemsFields: {
            thumb:"delving_thumbnail",
            title:"dc_title"
        },
        useAdvancedSearch: false,
        advancedSearch : {
            fields : [
                {name: "dc_title", label: "Titel"},
                {name: "dc_type", label: "Materiaal"},
                {name: "dc_date", label: "Periode"},
                {name: "dc_description", label: "Beschrijving"},
                {name: "dc_subject", label: "Onderwerp"}
            ]
        }
    });
});

