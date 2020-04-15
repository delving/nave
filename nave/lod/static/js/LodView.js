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

LodView.itemLevelNav = function () {
    if(!Store){return;} // depends on vs.store.js     
    
    function getParams (url) {
        var params = {};
        var parser = document.createElement('a');
        parser.href = url;
        var query = parser.search.substring(1);
        var vars = query.split('&');
        for (var i = 0; i < vars.length; i++) {
            var pair = vars[i].split('=');
            params[pair[0]] = decodeURIComponent(pair[1]);
        }
        return params;
    };
    
    var resultsQuery = window.atob(Store.get('itemNavResultsQuery'));    
    // set the back button href
    var backButton = document.querySelector('#btn-back');
    backButton.href=String(resultsQuery);
    // if we are coming from a virtual collection then exit
    if(resultsQuery.indexOf('/vc/') > -1 || resultsQuery.indexOf('/vw/') > -1){return;}    
    // update return link with the resultsQuery
    // get the array of navigation paths
    var navTree = JSON.parse(Store.get('itemNavTree'));
    // get the last page
    var lastPage = Store.get('itemNavLastPage');
    // set the current location
    var currentLocation = window.location;
    // turn the resultsQuery into a url object and extract params
    var resultsQueryObject = new Object(getParams(resultsQuery));  
    var currentPageNr;
    // console.log("resultsQueryObject", resultsQueryObject);
    // console.log("resultsQueryObject.q", resultsQueryObject.q.length)
    // console.log("resultsQueryObject.q.length", resultsQueryObject.q.length)
    // console.log("resultsQueryObject.hasOwnProperty", resultsQueryObject.hasOwnProperty('q'));
    if(!resultsQueryObject.hasOwnProperty('q')) {
        resultsQuery = resultsQuery + "?q=";         
    }
    if(resultsQueryObject.hasOwnProperty('page')){
        resultsQuery = resultsQuery;
        currentPageNr = resultsQueryObject.page
    }
    else {
        resultsQuery = resultsQuery + "&page=1"
        currentPageNr = 1;
    }
    var reAg = /\/aggregation\/(.*)/g;
    var currentItemPath = reAg.exec(currentLocation);
    var currentIndex = navTree.indexOf(currentItemPath[1]);    
    var appendTarget = document.getElementById('nav-return-button');
    var itemNavMarkup = '<ul class="nav nav-pills pull-left">' +
    '<li><a href="#previous" class="item-nav item-nav-prev" data-direction="previous">&laquo;&laquo; Vorige</a></li>' +
    '<li><a href="#next" class="item-nav item-nav-next" data-direction="next">Volgende &raquo;&raquo; </a></li>' +
    '</ul>';
    appendTarget.insertAdjacentHTML('afterend', itemNavMarkup);
    var itemNavButtons = document.querySelectorAll('.item-nav');

    if (parseInt(currentPageNr) === 1 && parseInt(currentIndex) === 0 ){
        document.querySelector('.item-nav-prev').classList.add('disabled');
    }

    if (parseInt(currentPageNr) === lastPage && parseInt(currentIndex) === navTree.length-1){
        document.querySelector('.item-nav-next').classList.add('disabled');
    }

    Array.prototype.forEach.call(itemNavButtons, function(nav){
        nav.addEventListener('click', function(e){
            e.preventDefault();
            var navDirection = nav.getAttribute('data-direction');
            var navTo = null;

            // set the next and previous items from the navTree
            if(navDirection === 'next'){
                navTo = navTree[Number(currentIndex)+1];
            }
            else {
                navTo = navTree[Number(currentIndex)-1];
            }    
            // if found in the navTree then go
            if(navTo && navTo !== undefined){
                // go to the next or previous item page
                window.location.href = "/resource/aggregation/"+navTo;
            }                        
            // else make a new navTree with an api query to the next or previous page
            else {
                // first we need a new query for results (this is an api query so dif url then the resultsQuery)
                var pageNr = '';                
                // set the page parameter with the correct number                
                if (navDirection === 'next') {
                    pageNr = parseInt(currentPageNr)+parseInt(1);
                }
                else {
                    pageNr = parseInt(currentPageNr)-parseInt(1);
                }

                // set the new page number for the return url
                var rePage = new RegExp("&page=\\d+");
                var newQsPage = resultsQuery.replace(rePage,'&page='+pageNr);
                Store.set('itemNavResultsQuery', window.btoa(newQsPage));
                
                // get the new questring only to build a new api url
                var parser = document.createElement("a");
                var newQs;
                parser.href = newQsPage;             
                if(!parser.search){
                    newQs = "?query=*:*";
                } else {
                    newQs = parser.search;
                }        
                var apiUrl = window.location.protocol +"//"+ window.location.host + "/api/search/v2/" + newQs + "&format=json";
                
                // if this is a virtual collection then we need a different api path
                if(newQsPage.indexOf('/vc/') > -1 || newQsPage.indexOf('/vw/') > -1){
                    apiUrl = newQsPage.replace('/search/',"/api/search/v2/")+"&format=json";
                }                
                // console.log("get new data");             
                // console.log("navTree",navTree);
                // console.log("navTo", navTo);
                // console.log("pageNr", pageNr);
                // console.log("newQsPage", newQsPage);
                // console.log("newQs", newQs);
                // console.log("apiUrl", apiUrl);
                // return;
                /**************************************************/
                // TODO: build apiUrl for a virtual collection
                /**************************************************/
                // do background api query to build a new nav stack
                var xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function () {
                    // Only run if the request is complete
                    if (xhr.readyState !== 4) return;
                    // Process our return data
                    if (xhr.status >= 200 && xhr.status < 300) {
                        // success              
                        var data = JSON.parse(xhr.response);
                        var newItemNavStack = data.result.items.map(function (item, index){
                            // console.log("item.item", item.item);
                            var entry = item.item.fields.system.about_uri;
                            // console.log(entry);
                            var reAg = /\/aggregation\/(.*)/g;
                            var newItemPath = reAg.exec(entry);
                            return newItemPath[1];
                        });
                        // create a new nav tree
                        Store.set('itemNavTree', JSON.stringify(newItemNavStack));

                        if(navDirection === 'next'){
                            navTo = newItemNavStack[0];
                        }
                        else {
                            navTo = newItemNavStack[newItemNavStack.length -1];
                        }
                        if(navTo !== undefined){
                            // go to the next or previous item page
                            window.location.href = "/resource/aggregation/"+navTo;
                        }
                    } else {
                        // failure
                        console.log("xmlHttpRequest failed", xhr);
                    }
                };
                // Create and send a GET request
                xhr.open('GET', apiUrl);
                xhr.send();                
            }            
        });
    });    
}   