function create_timeseries_chart(id = null, series = null, title = null) {
  Highcharts.setOptions({ lang: { thousandsSep: ',' } });
  // Create the chart
  Highcharts.stockChart(id, {
    rangeSelector: {
      selected: 1
    },

    title: {
      text: title
    },

    series: series,
    tooltip: {
      valueDecimals: 2
    }
  });
};

function toggle_table_visibility() {
  $('#table-warning').toggleClass('d-none');
  $('#large-table').toggleClass('d-none');

  text = $('#table-button').text()
  $('#table-button').text(text == "Hide Table" ? "Show Table" : "Hide Table")
}