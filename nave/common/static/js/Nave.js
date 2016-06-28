function Nave(){};

Nave.setTargetBlankToExternalUris = function () {
    var here = location.hostname;
    //TODO: fix this before using!
    $('a[href^="http://"], a[href^="https://"]').not('a[href*='+ here +']').attr('target','_blank');
};

/***********************************************************************************/
// Nave.initPopoverLink depends on bootstrap.js
/***********************************************************************************/
Nave.initPopoverLink = function (elem) {
    elem.popover({ trigger: "manual" , html: true, animation:false, container: 'body'})
        .on("mouseenter", function () {
            var _this = this;
            $(this).popover("show");
            $(".popover").on("mouseleave", function () {
                $(_this).popover('hide');
            });
        }).on("mouseleave", function () {
            var _this = this;
            setTimeout(function () {
                if (!$(".popover:hover").length) {
                    $(_this).popover("hide");
                }
            }, 300);
        }).on('click', function() {
            // todo: launch new query with term
        }
    );
};

/***********************************************************************************/
// Nave.initTooltip depends on bootstrap.js
/***********************************************************************************/
Nave.initTooltip = function () {
    $('[data-toggle="tooltip"]').tooltip()
};


/***********************************************************************************/
// Nave.initMapSearchModal depends on bootstrap.js and{% leaflet %} tags being loaded
/***********************************************************************************/
Nave.initMapSearchModal = function () {
    // Instantiate leaflet map
    //var modalMap = L.map('modalMapContainer').setView([59.95, 10.75], 3);

    var modalMap = L.map('modalMapContainer', {
        center: [59.95, 10.75],
        zoom: 3
    });

    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',{maxZoom:16}).addTo(modalMap);

    // Define function setBounds to populate the search submit form in the modal:
    var setBounds = function(bounds) {
        $('#max_x').val(bounds._northEast.lat);
        $('#max_y').val(bounds._northEast.lng);
        $('#min_x').val(bounds._southWest.lat);
        $('#min_y').val(bounds._southWest.lng);
        //console.log(bounds);
        //console.log('max_x',bounds._northEast.lat);
        //console.log('max_y',bounds._northEast.lng);
        //console.log('min_x',bounds._southWest.lat);
        //console.log('min_y',bounds._southWest.lng);
    };

    // When the modal is instantiated:
    $('#mapSearchModal').on('shown.bs.modal', function(){
        setTimeout(function() {
            modalMap.invalidateSize();
        }, 1);
        bounds = modalMap.getBounds();
        setBounds(bounds);

    });

    // When zoomining in or out on the map
    modalMap.on('moveend', function() {
        bounds = this.getBounds();
        setBounds(bounds);
    });

};


/***********************************************************************************/
// Nave.initSidePanel depends on jquery to be loaded. Toggles side panel
/***********************************************************************************/
Nave.toggleSidePanel = function () {
    // unbind click since function can be initiated multiple times
    $(".side-panel-tab").unbind('click').click(function(e){
        e.preventDefault();
        $(this).parent().toggleClass("open");
    });
};

Nave.initSidePanel = function () {
    Nave.toggleSidePanel ();
    // close on escape key
    $(document).keyup(function(e) {
        if (e.keyCode == 27) {
            $(".side-panel").removeClass("open");
        }
    });
};

