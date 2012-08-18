$('#add_member_button').click(function() {
    $('#add_member').slideToggle();
});

$('#add_member form').ajaxForm({
    dataType: 'json',
    success: function(data) {
        if (data.error) {
            alert(data.error);
        } else {
            $('#add_member').slideUp();
            $('#member_table').append(data.new_row);
        }
    }
});
