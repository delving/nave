function Ugc() {}

// Thank you Stack Overflow
// http://stackoverflow.com/questions/1184624/convert-form-data-to-javascript-object-with-jquery
$.fn.serializeObject = function()
{
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
};

Ugc.initForm = function () {

    var $ugcForm = $('#enrichment_link_form');
    if($ugcForm.length) {
        // define input form
        var $input_form =  $ugcForm;
        // set the value of the 'published' checkbox field with check/uncheck
        $('#id_published').change(function() {
            if(this.checked) {
                this.value = "True";
            }
            else {
                this.value = "False"
            }
        });
        // validate using parsley.js
        $input_form.parsley().on('field:validated', function() {
            var ok = $('.parsley-error').length === 0;
            $('.bs-callout-info').toggleClass('hidden', !ok);
            $('.bs-callout-warning').toggleClass('hidden', ok);
        })
        .on('form:submit', function() {
            return false;
        })
        .on('form:success', function(){
            // get authorization token
            var authToken = $.cookie('csrftoken');
            // get id value (if it's there)
            var id = $('#id_id').val();
            // set up the basic ugc object to send via api call
            var ugcObj = {
                'source_uri': $('#id_source_uri').val(),
                'content_type': $('#id_content_type').val(),
                'link': $('#id_link').val(),
                'name': $('#id_name').val(),
                'short_description': $('#id_short_description').val(),
                'published': $('#id_published').val()
            };
            // Extend the ugc object with id value if present (editting mode)
            if(id.length > 0) {
                var idObj = {'id': id}
                $.extend(ugcObj, idObj);
            }
            // Send it along when all is well
            if(authToken){
                Ugc.sendForm(ugcObj, authToken, id);
            }
        }).on('form:error', function(e) {
            alert('foo');
            console.log(e);
        });

        // trigger on edit
        $('.ugc-block-edit-button').on('click', function (e) {
            e.preventDefault();
            var block_source_Id = $(this).parents('form').attr('id');
            var $block_data_form = $('#'+block_source_Id);
            // toggle the side panel and populate the input fields with block data
            $.when(Nave.toggleSidePanel("#ugc-enrichment-side-panel")).then(function(){
                // retrieve and objectify block hidden form data
                var dataObj = $block_data_form.serializeObject();
                var formObj = $input_form.serializeObject();
                $.each(dataObj, function(dKey, dValue){
                    var $input = $input_form.find('[name="'+dKey+'"]'),
                        type = $input.attr('type');
                    $.each(formObj, function(fKey, fValue){
                        switch(type) {
                            case 'checkbox':
                                if(dValue === "True"){
                                    $input.attr('checked', true);
                                }
                                else {
                                   $input.attr('checked', false);
                                }
                                $input.val(dValue);
                                break;
                            default:
                                $input.val(dValue);
                        }
                    });
                });
            });
            return false;
        });
    }
};


Ugc.sendForm = function (ugcObj, authToken, id) {
    var api_url = '/api/enrich/ugc/';
    var api_type = 'POST'
    if(id && id.length > 0 ){
        api_url = '/api/enrich/ugc/'+id+'/';
        api_type = 'PUT'
    }
    $.ajax({
        type: api_type,
        url: api_url,
        data: ugcObj,
        beforeSend : function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", authToken);
            xhr.setRequestHeader("Accept","application/json");
        },
        success: function () {
            Nave.toggleSidePanel("#ugc-enrichment-side-panel");
            setTimeout(function(){
                location.reload()
            }, 750);
        },
        //TODO: i18n of error messages might by nice to have
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            var errors = XMLHttpRequest.responseJSON;
            console.log(errors);
            if (errors){
                var link_exists = errors['non_field_errors'].indexOf("De velden source_uri, link moeten een unieke set zijn.");
                $('.bs-callout-info').toggleClass('hidden', 1);
                $('.bs-callout-warning').toggleClass('hidden', 0);
                $('input#id_link').toggleClass("parsley-error");
                if (link_exists > -1) {
                    $('.bs-callout-warning').append("De URL/Link bestaat al voor deze pagina");
                }
            }
            return false;
        }
    });
};

