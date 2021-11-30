function create_timeseries_chart(id=null, data=null, title=null, series_name=null) {
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