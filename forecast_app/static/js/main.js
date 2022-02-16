function create_timeseries_chart(id = null, data = null, title = null, series_name = null) {
  Highcharts.setOptions({ lang: { thousandsSep: ',' } });
  // Create the chart
  Highcharts.stockChart(id, {
    rangeSelector: {
      selected: 1
    },

    title: {
      text: title
    },

    series: [{
      name: series_name,
      data: data,
      tooltip: {
        valueDecimals: 2
      }
    }]
  });
};

function toggle_table_visibility() {
  $('#table-warning').toggleClass('d-none');
  $('#large-table').toggleClass('d-none');

  text = $('#table-button').text()
  $('#table-button').text(text == "Hide Table" ? "Show Table" : "Hide Table")
}