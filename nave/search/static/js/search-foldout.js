//ON DOM READY

$(function(){
    // grid necessities
    var winsize;
    var $window = $(window);
    var $body = $('html, body');


    $('a.result-item-link').on('click', function(e){
        // don't go anywhere
        e.preventDefault();
        // if this is already active then close it
        if($(this).parent().parent().hasClass('current')) {
            fo_container.children().removeClass('active-row current last');
            $('.result-item-foldout').remove();
            return;
        }

        // first reset everything: remove the foldout
        $('.result-item-foldout').remove();
        // remove the current row classes
        fo_container.children().removeClass('active-row current last active');
        // set the current grandparent container to 'current'
        $(this).parent().parent().addClass('current');
        // get index from html data attr.
        var index = $(this).data('index');
        // send id along with load request
        var slug = $(this).data('slug');
        var doc_type = $(this).data('doc_type');
        var acceptance_mode = $(this).data('mode');
        // determine the row
        var row = Math.floor(index / fo_cols);
        // and the elements in the row
        var $row_objects = fo_result_obj.slice(row * fo_cols, (row + 1) * fo_cols);
        // for each element in the current row add functional classes
        $.each($row_objects, function(index){
            $(this).parent().addClass('active-row');
            if((index + 1) === $row_objects.length){
                $(this).parent().after('<div class="col-sm-12 result-item-foldout"><div class="result-item-detail"></div></div>');
            }
        });
        // append the foldout html to the last elem in the row
        var dataTarget = $('.result-item-detail');
        dataTarget.load(fo_endpoint+doc_type+"/"+slug+"?mode="+acceptance_mode);

        // scroll up above the fold
        var offset = dataTarget.offset().top;
        var scrollDistance = offset-200;//show part of the row above to be able to navigate
        $("html, body").animate({ scrollTop: scrollDistance }, 1000);


        // Call functionality to retrieve linked data on mouseover
        setTimeout(function(){
            $('#search-foldout-close').on('click', function () {
                $('.result-item-foldout').remove();
                // remove the current row classes
                fo_container.children().removeClass('active-row current last active');
            });
            LodView.initPopovers(); // needs LodView.js to be loaded
        },500);

    });
});