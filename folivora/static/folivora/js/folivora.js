$('#add_member_button').click(function() {
    $('#add_member').slideToggle();
});

$('#add_dependency_button').click(function() {
    $('#add_dependency').slideToggle();
});

$('#id_projectmember_set-__prefix__-state').removeAttr('required');

$('#add_member form').ajaxForm({
    dataType: 'json',
    success: function(data) {
        if (data.error) {
            alert(data.error);
        } else {
            $('#add_member').slideUp();
            var new_row = $('#empty_member_row').clone(true);
            $(new_row).removeAttr('id').show();
            $('#empty_member_row').parent().append(new_row.html().replace(/__prefix__/g, data.id).replace(/USERNAME/g, data.username));
            new_row.show()
            var form_idx = $('#id_projectmember_set-TOTAL_FORMS').val();
            $('#id_projectmember_set-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        }
    }
});
