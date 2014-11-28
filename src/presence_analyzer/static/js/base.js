function get_users(users_view_url, onSelected) {
    google.load("visualization", "1", {packages:["corechart", "timeline"], 'language': 'pl'});
    (function($) {
        $(document).ready(function() {
            var loading = $('#loading'),
                avatars = {};
            $.getJSON(users_view_url, function(result) {
                var dropdown = $("#user_id");
                $.each(result, function(item) {
                    dropdown.append($("<option />").val(this.id).text(this.name));
                    avatars[this.id] = this.avatar;
                });
                dropdown.show();
                loading.hide();
            });
            $('#user_id').change(function() {
                var selected_user = $("#user_id").val(),
                    chart_div = $('#chart_div');

                try {
                    document.getElementById('image').src = avatars[selected_user];
                }
                catch (e) {
                    var img = new Image(),
                        avatardiv = document.getElementById('avatar');

                    img.src = avatars[selected_user];
                    img.id = 'image';
                    avatardiv.appendChild(img);
                }

                chart_div.hide();
                $('#error-text').hide();
                if (selected_user === '-1') {
                    $('#avatar').hide();
                } else {
                    loading.show();
                    onSelected(loading, chart_div, selected_user);
                    $('#avatar').show();
                }
            });
        });
    })(jQuery);
};
