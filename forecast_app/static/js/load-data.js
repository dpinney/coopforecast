function toggle_table_visibility() {
	$('#table-warning').toggleClass('d-none');
	$('#large-table').toggleClass('d-none');

	text = $('#table-button').text()
	$('#table-button').text(text == "Hide Table" ? "Show Table" : "Hide Table")
}