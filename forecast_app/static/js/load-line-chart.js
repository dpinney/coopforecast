function create_timeseries_chart(id=null, data=null, title=null) {
  // Create the chart
  Highcharts.stockChart(id, {
    rangeSelector: {
      selected: 1
    },

    title: {
      text: title
    },

    series: [{
      data: data,
      tooltip: {
        valueDecimals: 2
      }
    }]
  });
};