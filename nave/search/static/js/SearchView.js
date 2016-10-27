// globals for foldout functionality
var fo_result_obj, fo_container, fo_endpoint, fo_cols;
// globals for leaflet map functionality
var tiles, map;

function SearchView(){};

/***********************************************************************************/
// SearchView.initViewTabs requires
// Sets the localStorage/cookie 'view' to maintain last opened tab on page nav
/***********************************************************************************/
SearchView.initViewTabs = function () {
    //$('a[data-toggle="view"]').on('click', function (e) {
    //    $.cookie('view', $(e.target).attr('data-view'));
    //});
};

/***********************************************************************************/
// SearchView.initPagination requires search/static/js/search-foldout.js
// Sets the global variables necessary for the foldout functionality
/***********************************************************************************/
SearchView.initFoldout = function (nr_cols, language) {
    var cols = 4;
    if(nr_cols) {
        cols = nr_cols;
    }
    fo_result_obj = $('.results-grid-item');
    fo_container = $('.results-grid');
    if (language) {
        fo_endpoint = '/'+language+'/detail/foldout/';
    }
    else {
        fo_endpoint = '/detail/foldout/';
    }
    fo_cols =  cols;

};

/***********************************************************************************/
// SearchView.process requires common/static/js/imageLiquid.js
// Resize an image to fit its container and gives some control over the positioning
/***********************************************************************************/
SearchView.processImages = function () {
    $(".media").imgLiquid({
        fill: true,
        horizontalAlign: "center",
        verticalAlign: "center",
        useBackgroundSize: false
    });
};

/***********************************************************************************/
// SearchView.initFacets requires search/static/js/search-facets-sort.js
/***********************************************************************************/
SearchView.initFacets = function () {
    $(".facet-container .sort").on('click', function (e) {
        e.preventDefault();
        var _this = $(this),
            target = _this.data('id'),
            type = _this.data('sort-type');
        sortFacets(_this, target, type);
    });
    // facet link tooling
    $.each($('ul.list-facets'), function(){
        var facets = $(this);
        var links = facets.find('a.facet-link');
        var container = facets.closest('.facet-container');
        var facet_body = container.find('.facet-body');
        var facet_list = container.find('.facet-list');
        var facet_tools = container.find('.facet-tools');
        var facet_toggle = container.find('.facet-toggle');

        if(links.length <= 3 ){
            $(facet_tools).hide();
        }

        // href fixing where necessary
        $.each(links, function(){
            var link = $(this),
                href = link.attr('href'),
                newHref = '';
            if (href.indexOf(' & ') > 0){
                newHref = href.replace(' & ', '%20%26%20');
                link.attr('href', newHref);
            }
        });

        // check for first checked facet and scroll it into view, then break out of loop
        $.each(links, function(){
            var link = $(this);
            if(link.attr('data-checked')=='true'){
                // if container has a selected facet then add class 'in' to open
                facet_body.addClass('in');
                // set the correct icon
                container.find('i').toggleClass('fa-minus fa-plus');
                // scroll to the first selected facet link
                facet_list.animate({scrollTop: link.offset().top - container.offset().top - 80 });
                // then stop
                return false;
            }
        });

        facet_toggle.on('click', function(){
            $(this).find('i').toggleClass('fa-minus fa-plus');
        });

    });
};

/***********************************************************************************/
// SearchView.initSearchTags - depends on search/static/js/bootstrap-taginputs.js
// creates "tags" for inputted search strings and selected facets
/***********************************************************************************/
SearchView.initSearchTags = function() {
    var $queryForm = $('#form-query-fields');
    var $input = $('div#qtags');
    var $btnClear = $('#btn-clear-simple-search');
    $input.tagsinput({
        itemText:'text',
        itemValue:'value',
        trimValue: true,
        tagClass: function (item) {
            var classStr = 'label label-default';
            switch (item.name) {
                case 'q':
                    classStr = 'label label-query ';
                    return classStr;
                case 'qf':
                    classStr = 'label label-facet ';
                    return classStr;
            }
        }
    });

    $queryForm.find('input:hidden').each(function() {
        var $param = $(this);
        var $qTerms = [];
        if ($param.attr('name') == 'q') {
            if ($param.val().length > 0){
                // first trim whitespace then split into array
                qTerms = $param.attr('value').replace(/^\s+|\s+$/gm,'').split(' ');
                // add each element in the array
                qTerms.forEach(function(element){
                    $input.tagsinput('add', {'text': element, 'value': element, 'name': $param.attr('name')});
                });
            }
        }
        else {
            $input.tagsinput('add', {'text': $param.attr('data-text'), 'value': $param.attr('value'), 'name': $param.attr('name')});
        }
    });

    $btnClear.removeClass('hidden');
    // clean all queries and start fresh
    $btnClear.on('click', function () {
        $.when(
            $input.tagsinput('removeAll'),
            $queryForm.find('input:hidden').remove()
        ).done(function () {
            $queryForm.submit();
        });
    });

    // remove a specific item from the hidden form for a new query
    $input.on('beforeItemRemove', function(event) {
        var _value = event.item.value;
        $queryForm.find(':input').each(function(){
            var _this = $(this);
            // no special actions needed for facet just remove
            if( _this.val() == _value && _this.attr('name') == 'qf' ){
                _this.remove();
            }
            if ( _this.attr('name') == 'q') {
                // be kinds and always trim
                _q = _this.val().trim();
                // nr of terms in the query
                _nrTerms = _q.split(/\s+/).length;
                // remove one query term from within string of multiple terms
                if ( _nrTerms > 1 && _q.toLowerCase().indexOf(_value.toLowerCase()) >= 0 ) {
                    _this.val(_this.val().replace(_value,''));

                }
                // remove the single query term
                else if ( _nrTerms == 1 ) {
                    _this.remove();
                }
            }
        });
        $queryForm.submit();
    });
};

/***********************************************************************************/
// SearchView.checkGeoCount: hide geo tab if no geo points are found.
// Will also hide the grid tab because it has become redundant.
/***********************************************************************************/
SearchView.checkGeoCount = function (queryStr) {
    if(queryStr){
        $.getJSON("/search/?format=geojson&cluster.factor=1&" + queryStr, function (data) {
            if(!data.features.length) {
                $('#tab-geo, #tab-grid').hide();
            }
        });
    }
};


/***********************************************************************************/
// SearchView.initGeo requires {% leaflet_js %} and {%leaflet_css %} to be loaded
/***********************************************************************************/
SearchView.initGeo = function () {

    // init leaflet map
    tiles = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',{maxZoom:22});
    map = L.map('ds-map',  { layers: [tiles] });

    // function buildMap(mapReceiver) {
    // $.getJSON("/search/?format=geojson&cluster.factor=1&" + queryStr, function (data) {
    //     // first check if there is any data
    //     if(data.features.length && data.features.length > 0){
    //         var centerPoint = L.latLng(51.55, 0); // default should not be necessary
    //         if (data.features.length == 1) {
    //             var feature = data.features[0];
    //             centerPoint = L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
    //         }
    //         //console.log("set view to center point", centerPoint);
    //         map.setView([centerPoint.lat, centerPoint.lng], 5);
    //         var featureGroup = new L.FeatureGroup();
    //         featureGroup.addTo(map);
    //         var markerClusterGroup = new L.MarkerClusterGroup();
    //         markerClusterGroup.addTo(map);
    //         mapReceiver(featureGroup, markerClusterGroup)
    //     }
    //     // if there is no data then hide geo functionality
    //     else {
    //         $('#tab-geo, #tab-grid').hide();
    //     }
    // });
    // }

    buildMap(function(featureGroup, markerClusterGroup) {

        map.on('moveend', queryForPoints);
        // hack: the map inside a tab pane is not sized properly when tab is opened.
        $("body").on('shown.bs.tab','#show-map', function() {
            map.invalidateSize(false);
        });

        var featureLayer, clusterLayer;
        var minFactor = 0.0;
        var factor = 1.0;

        function queryForPoints() {
            var bounds = map.getBounds();
            var westToEast = Math.abs(bounds._northEast.lng - bounds._southWest.lng);
            var FACTOR_FUNCTION = [
                [0.2, minFactor],
                [0.4, 0.55],
                [0.8, 0.64],
                [1.6, 0.67],
                [3.2, 0.70],
                [6.4, 0.73],
                [12.8,0.80],
                [40.0, 1]
            ];
            var distance = 1000;
            for (var walk=0; walk<FACTOR_FUNCTION.length; walk++) {
                var proximity = Math.abs(FACTOR_FUNCTION[walk][0] - westToEast);
                if (proximity < distance) {
                    distance = proximity;
                    factor = FACTOR_FUNCTION[walk][1];
                }
            }
            //                console.log("westToEast=" + westToEast +" factor=" + factor);
            //var boundsQueryString = "&min_x="+bounds._southWest.lat+"&min_y="+bounds._southWest.lng+"&max_x="+bounds._northEast.lat+"&max_y="+bounds._northEast.lng;
            //$.getJSON("/search/?format=geojson&cluster.factor=" + factor + "&" + queryStr + boundsQueryString, showGeo);
            // $.getJSON("/search/?format=geojson&cluster.factor=" + factor + "&" + queryStr, showGeo);
        }

        function showGeo(data) {
            if (featureLayer && featureGroup.hasLayer(featureLayer)){
                //                   console.log("removing feature layer");
                featureGroup.removeLayer(featureLayer);
                featureLayer = undefined;
            }
            if (clusterLayer) {
                //                    console.log("markerClusterGroup.hasLayer(clusterLayer):" + markerClusterGroup.hasLayer(clusterLayer), clusterLayer);
                //                    the call to hasLayer here returns false when it should not
                //                if (clusterLayer && markerClusterGroup.hasLayer(clusterLayer)) {
                //                    console.log("removing cluster layer");
                markerClusterGroup.removeLayer(clusterLayer);
                clusterLayer = undefined;
            }
            if (factor == minFactor) {
                function getPointData() {
                    var m = $(this)[0].feature;
                    var id = m.id;
                    var doc_type = m.properties.doc_type;
                    var url = "/resolve/" + doc_type + "/" + id;
                    console.log('getPointData');
                    $.get( url, function( data ) {
                        //todo: returned data should fill the marker bindPopup or do something similar to a foldout
                        console.log(data);
                    });
                }

                clusterLayer = L.geoJson(data, {
                    pointToLayer: function(feature, latlng) {
                        //                            console.log('clusterLayer > pointToLayer');
                        console.log('point to layer');
                        var count = feature.properties.count.toString();
                        var id = feature.id;
                        var doc_type = feature.properties.doc_type;
                        // todo: the URL should point to the object
                        var url = "/resolve/" + doc_type + "/" + id;
                        //                        showMe(url);
                        var marker = L.marker(latlng).on('mouseover', getPointData);
                        return marker.bindPopup('<a href="' + url + '">' + id.replace("dcn_", " ").replace("_", " ") + '</a>');
                    }
                });
                markerClusterGroup.addLayer(clusterLayer);
                //                    console.log("markerClusterGroup has clusterLayer now", clusterLayer);
            }
            else {
                featureLayer = L.geoJson(data, {
                    pointToLayer: function(feature, latlng) {
                        var count = feature.properties.count.toString();
                        var markerClass = 'marker-cluster-small';
                        if (count > 50 ) {
                            markerClass = 'marker-cluster-medium';
                        }
                        return L.marker(latlng, {
                            icon: L.divIcon({
                                className: 'marker-cluster '+markerClass,
                                iconSize: L.point(26,26),
                                html: '<div>' + feature.properties.count.toString() + '</div>'
                            })
                        });
                    }
                });
                featureGroup.addLayer(featureLayer);
            }
        }
    });
};
