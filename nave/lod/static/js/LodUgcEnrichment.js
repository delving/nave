function Ugc() {}

Ugc.initForm = function () {
    $('#enrichment_link_form').parsley().on('field:validated', function() {
        var ok = $('.parsley-error').length === 0;
        $('.bs-callout-info').toggleClass('hidden', !ok);
        $('.bs-callout-warning').toggleClass('hidden', ok);
    })
    .on('form:submit', function(e) {
        return false;
    })
    .on('form:success', function(){
        var authToken = $.cookie('csrftoken');
        var ugcObj = {
            'source_uri': $('#id_source_uri').val(),
            'link': $('#id_link').val(),
            'name': $('#id_name').val(),
            'short_description': $('#id_short_description').val(),
            'content_type': $('#id_content_type').val(),
            'published': $('#id_published').val(),
        };
        if(authToken){
            Ugc.sendForm(ugcObj, authToken);
        }
    });
};

Ugc.sendForm = function (ugcObj, authToken) {
    $.ajax({
        type: 'POST',
        url: '/api/enrich/ugc/',
        data: ugcObj,
        beforeSend : function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", authToken);
        },
        success: function () {
            console.log('form sent!');
        },
        error: function (e) {
            console.log(ugcObj);
            console.log(e);
        }
    });
};

