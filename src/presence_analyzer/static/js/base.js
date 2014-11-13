function get_users(users_view_url, onSelected) {
    google.load("visualization", "1", {packages:["corechart", "timeline"], 'language': 'pl'});
    (function($) {
        $(document).ready(function() {
            var loading = $('#loading');
            $.getJSON(users_view_url, function(result) {
                var dropdown = $("#user_id");
                $.each(result, function(item) {
                    dropdown.append($("<option />").val(this.user_id).text(this.name));
                });
                dropdown.show();
                loading.hide();
            });
            $('#user_id').change(function() {
                var selected_user = $("#user_id").val(),
                    chart_div = $('#chart_div');

                if (selected_user) {
                    loading.show();
                    chart_div.hide();
                    onSelected(loading, chart_div, selected_user);
                }
            });
        });
    })(jQuery);
};
