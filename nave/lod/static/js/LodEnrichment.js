function LodEnrichment() {}

LodEnrichment.initForm = function () {
    $('#enrichment_link_form').on('submit', function(e) {
        e.preventDefault();
        LodEnrichment.validateForm();
    });
};

LodEnrichment.validateForm = function () {
    console.log('Ready to validate');
    LodEnrichment.sendForm();
};

LodEnrichment.sendForm = function () {
    $.ajax({
        type: 'POST',
        url: './lod-detail/enrichement/', // TODO: route and functionality
        data: {
            'enr_type': $('#enr_type').val(),
            'enr_name': $('#enr_name').val(),
            'enr_description': $('#enr_description').val(),
            'enr_link': $('#enr_link').val(),
        },
        success: function () {
            console.log('form sent!');
        }
    });
};