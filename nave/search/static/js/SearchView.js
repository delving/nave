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
SearchView.processImages = function (fill) {
    var fillImage = true;
    if(fill){
        fillImage = fill;
    }
    $(".media").imgLiquid({
        fill: fillImage,
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
            // if (href.indexOf('qf=') > 0){
            //     newHref = href.replace('qf=', 'qf=[]');
            //     link.attr('href', newHref);
            // }
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
                case 'qf[]':
                    classStr = 'label label-facet ';
                    return classStr;
                case 'qf%5B%5D':
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
                $qTerms = $param.attr('value').replace(/^\s+|\s+$/gm,'').split(' ');
                // add each element in the array
                $qTerms.forEach(function(element){
                    $input.tagsinput('add', {
                        'text': element,
                        'value': element,
                        'name': $param.attr('name')
                    });
                });
            }
        }
        // show other facet fields except min and max coordinates from the modal maps search
        else if (!(/\bmin/i.test($param.attr('name')) || /\bmax/i.test($param.attr('name')))) {
            var text = $param.attr('data-text');
            var value =  $param.attr('value');
            var name =  $param.attr('name');
            //todo: internationalize
            var re = /((hasDigitalObject)|(hasCoordinate))/;
            if(re.test(value)){
                text = value.replace(/nave_hasDigitalObject/g, "Digital Object").replace(/nave_hasCoordinates/g, "Coordinates");
            }
            $input.tagsinput('add', {
                'text': text,
                'value': value,
                'name': name
            });
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
        event.preventDefault();
        var _value = event.item.value;
        $queryForm.find(':input').each(function(){
            var _this = $(this);
            if( _this.val() == _value && _this.attr('name') == 'qf[]' || _this.attr('name') == 'qf' ){
                _this.remove();
                return false;
            }
            if ( _this.attr('name') == 'q' ) {
                // query = value so just remove
                if( _this.val() == _value){
                    _this.remove();
                    return false;
                }
                else {
                    // be kinds and always trim
                    var _q = _this.val().trim();
                    // nr of terms in the query
                    var _nrTerms = _q.split(/\s+/).length;
                    // remove one query term from within string of multiple terms
                    if ( _nrTerms > 1 && _q.toLowerCase().indexOf(_value.toLowerCase()) >= 0 ) {
                        _this.val(_this.val().replace(_value,''));

                    }
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

};
