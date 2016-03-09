function LodView() {}

//############################################################}
// Add proper classes to tabs and panes                      #}
//############################################################}
LodView.initNavTabs = function () {
    $('.navigator-tabs li:first-of-type').addClass('active');
    $('.navigator-tabs .tab-pane').first().addClass('active');
};


//############################################################}
// show predicate uris                                       #}
//############################################################}
LodView.initProperties = function (){
    $('#display-predicate-uri-label').on('click', function(){
        $('.predicate-uri-label').toggle();
    });

    // toggle inline data                                        #}
    if($('.js-with-inlines').length){
        $('.js-with-inlines').on('click', function(e) {
            e.preventDefault();
            var target = $('#'+$(this).attr('data-target'));
            target.toggleClass('hidden');
            $(this).toggleClass('collapsed');
            if( $(this).hasClass('collapsed') ) {
                $(this).html($(this).attr('data-more-text'));
            } else {
                $(this).html($(this).attr('data-less-text'));
            }
        });
    }
};


//############################################################}
// mouseover i icon for more info/definition                 #}
//############################################################}
LodView.initPopovers = function () {
    $('.js-lod-popover-trigger').popover({
        html: true,
        trigger: 'hover',
        content: function () {
            return $(this).next('.js-lod-popover-content').html();
        }
    });
};

//############################################################}
// click media image for fullscreen view                     #}
//############################################################}
LodView.initFullscreen = function () {
    $('a.fullscreen').fullsizable();
    $(".imgLiquidFill").imgLiquid();
};


LodView.initLinkedPropertiesModal = function (e, elem) {
    // don't go anywhere, modal is being activated by this class
    e.preventDefault();
    // grab some display values for the modal header
    $('.current-fieldname').html(elem.attr('property'));
    $('.current-literal').html(elem.html());
    // grab data for the modal body
    var endpoint = $('#'+elem.attr('data-endpoint'));
    $("#linked-data-container" ).html( endpoint.html());
};


LodView.initGeo = function (points) {
    map.invalidateSize(false);
    setTimeout(function(){
        var bounds = new L.LatLngBounds(points);
        map.fitBounds(bounds, { padding: [50, 50] });
    });
};


LodView.initRelated = function (sourceUri) {

    $.get( '/search-lod-related/?q='+sourceUri, function( data ) {
        $("#related-results" ).html( data );
    });
    // internal function to iterate over facet links and change click behavior to stay on this page and just reload the related-results container #}
    var alterLinks = function () {

        setTimeout(function() {
            $(".pagination a").on('click', function (e) {
                e.preventDefault();
                $.get($(this).attr('href'), function( data ) {
                    $("#related-results" ).html( data );
                });
                alterLinks();
                setTimeout(function(){
                    $(".media").matchHeight();
                    $(".meta").matchHeight();
                }, 2500);
            });
        }, 500);
    };
    // call above function to change link behavior #}
    alterLinks();
};

/* load deepzoom */
LodView.loadDeepZoom = function (viewerName, zoomUri) {
    // script dependant on swfobject.js
    if (swfobject.hasFlashPlayerVersion("7")) {
        var flashvars = {
            'source': zoomUri
        };
        var params = {
            'allowfullscreen': 'true',
            'allowscriptaccess': 'always',
            'wmode': 'opaque'
        };
        var attributes = {
            'id': viewerName,
            'name': viewerName
        };
        swfobject.embedSWF('/static/flash/OpenZoomViewer.swf', viewerName, '100%', '400px', '7', 'false', flashvars, params, attributes);
    } else {
        // flash warning
    }
};