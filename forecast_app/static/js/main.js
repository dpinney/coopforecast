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
    },

    exporting: {
      csv: {
        // Replace column header name so that it can be automatically reingested
        columnHeaderFormatter: function (item, key, keyLength) {
          // HACK: Best logic I could come up with is the key is not defined for the x-axis
          return key ? item.name : 'timestamp';
        }
      }
    }
  });
};

function toggle_table_visibility() {
  $('#table-warning').toggleClass('d-none');
  $('#large-table').toggleClass('d-none');

  text = $('#table-button').text()
  $('#table-button').text(text == "Hide Table" ? "Show Table" : "Hide Table")
}