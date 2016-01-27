function SearchWidget() {}

/***********************************************************************************/
// SearchWidget.init depends on ZeroClipboard.js to be loaded
/***********************************************************************************/
SearchWidget.init = function (static_path) {
    // set path to swf
    ZeroClipboard.config( { swfPath: static_path+"flash/ZeroClipboard.swf" } );
    // create a clipboard client
    var client = new ZeroClipboard($(".copy-button"));
    // copy to clipboard
    client.on( "copy", function (event) {
        $('#msg-copied').toggleClass('hidden');
        setTimeout(function(){
            $('#msg-copied').toggleClass('hidden');
        },3000);
    });
    // update page form preview
    $('#btn-update-preview').on('click', function () {
       SearchWidget.updatePreview();
    });
    // load html into textarea
    $('#widgetCodeModal').on('show.bs.modal', function (event) {
        SearchWidget.createCode();
    });
    // todo: higlight preview form areas when associated input field in focus
};

SearchWidget.updatePreview = function () {
    var widget_text = $('#search-widget-text').val();
    var placeholder_text = $('#search-widget-placeholder-text').val();
    var button_text = $('#search-button-text').val();
    $('.search-widget-text').html(widget_text);
    $('.search-widget-input').attr('placeholder', placeholder_text);
    $('.search-widget-button').html(button_text);
};

SearchWidget.createCode = function () {
    var code = $('#widget-code-source').html();
    $('textarea#widget-code').val(code.trim());
};