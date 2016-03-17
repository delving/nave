{% load staticfiles future  %}

jQuery(document).ready(function($) {
    jQuery(document).delvingInstant({
        endPoint: "{{ endpoint }}",
        orgId: "{{ org_id }}",
        collectionSpecs: ["{{  diw.collection_spec }}"],
        dataOwner: "{{ diw.collection_spec }}",
        hasDigitalObject: false,
        rows: 10,
        configHelp: {{diw.show_config_help|lower}},
        resultsLayout: "list",
        defaultImg: "{% static 'img/blank.png' %}",
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
        linkToExternalLandingPage: false,
        textExpander: true,
        maxCharactersResults: "255",
        maxCharactersItem: "1000",
        maxCharactersTitle: 200,
        thumbnailWidth:"144",
        useDeepZoom: true,
        useFlashZoom: true,
        usePushState: false,
        deepZoomFlashFile: "{% static 'flash/OpenZoomViewer.swf' %}",
        thumbnailField: "delving_thumbnail",
        displayFacets: [
            {% for facet in diw.facets.all %}
                {name: "{{ facet.name }}", label: "{{ facet.label }}" }{% if not forloop.last %},{% endif %}
            {% endfor %}
        ],
        resultFields: [
            {% for field in diw.resultfields.all %}
                {name: "{{ field.name }}", label: "{% if field.label %}{{ field.label }}{% endif %}" }{% if not forloop.last %},{% endif %}
            {% endfor %}
        ],
        itemFields: [
            {% for field in diw.detailfields.all %}
                {name: "{{ field.name }}", label: "{% if field.label %}{{ field.label }}{% endif %}" }{% if not forloop.last %},{% endif %}
            {% endfor %}
        ],
        itemImageFields: {
            thumb:"delving_thumbnail",
            image:"europeana_isShownBy",
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
        }
    });
});