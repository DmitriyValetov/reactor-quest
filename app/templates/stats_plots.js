
window.onload = function() {
  google.charts.load("current", {
    packages: ["corechart", "line"]
  });
  google.charts.setOnLoadCallback(drawCharts);
};

function drawCharts(){
  fetchAllData(buildAllReceived);
}

function UpdateAllCharts(chart_holder){
    fetchAllData(function(responce){
      console.log('updating');
      console.log(responce);

      // scalars:
      var scalars_container = $('#forScalars');
          scalars_container.empty();
      var scalars_names = [];
      for(var k in responce.scalars) scalars_names.push(k);
      scalars_names.forEach(function(scalar_name){
        scalars_container.append(`
          <tr>
            <td>${scalar_name}</td>
            <td>${responce.scalars[scalar_name]}</td>
          </tr>
        `);
      });

      // time_series:
      var stats = [];
      for(var k in responce.time_series) stats.push(k);
        stats.forEach(function(stat_name){
          // var pair = chart_holder[stat_name];
          var chart_obj = chart_holder[stat_name][0],
              data_ = chart_holder[stat_name][1],
              options = chart_holder[stat_name][2];

          data_.jc = [];
          data_.wg = [];
          // data.jc.shift(); // labels
          // data.wg.shift(); // y values
          responce.time_series[stat_name].x.forEach(function(timeStr, i){
//            data_.addRow( [ moment.utc( (new Date(timeStr)).toString() ).format('hh:mm:ss').toString(), responce.time_series[stat_name].y[i] ] );
              data_.addRow( [ moment.utc(timeStr).local().format('hh:mm:ss'), responce.time_series[stat_name].y[i] ] );

          });
          chart_obj.draw(data_, options);
        
      });
      setTimeout(UpdateAllCharts, {{stats_update_timeout}}, chart_holder);
    });
  }

  function buildAllReceived(data){
    console.log('building first time');
    console.log(data);

    // scalars:
    var scalars_container = $('#forScalars');
        scalars_container.empty();
    var scalars_names = [];
    for(var k in data.scalars) scalars_names.push(k);
    scalars_names.forEach(function(scalar_name){
      scalars_container.append(`
        <tr>
          <td>${scalar_name}</td>
          <td>${data.scalars[scalar_name]}</td>
        </tr>
      `);
    });


    // time_series:
    var stats = [];
    for(var k in data.time_series) stats.push(k);

    var chart_holder = {};
    stats.forEach(function(stat_name){
      var container = document.getElementById('forCharts');
      var div = document.createElement('div');
      div.classList.add('chart-container');
      container.prepend(div);

      var chart_obj = new google.visualization.LineChart(div);
      var stats_data = data.time_series[stat_name];
      var options = createOptions(stat_name);
      var data_    = createData(stat_name, stats_data);
      chart_obj.draw(data_, options);
      chart_holder[stat_name] = [chart_obj, data_, options];
    });

    setTimeout(UpdateAllCharts, {{stats_update_timeout}}, chart_holder);
  }

  function createData(stat_name, stats_data) {
    var xs = stats_data.x.map(function(timeStr){ return moment.utc(timeStr).local().format('hh:mm:ss'); });
//    var xs = stats_data.x.map(function(timeStr){ return moment( (new Date(timeStr)).toString() ).format('hh:mm:ss').toString(); });
    var ys = stats_data.y;
    var data_list = xs.map(function(x, i){ return [x, ys[i]] });
    var data_ = google.visualization.arrayToDataTable([
      ["Time", stat_name],
      [(0).toString(), 0]
    ]);

    data_list.forEach(function(e){data_.addRow(e)});

    return data_; 
  }

  function createOptions(title) {
    return {
      title: title,
      hAxis: {
          title: "Time"
      },
      vAxis: {
          title: title
      }
    };
  }
    
  function addData(chart, label, data) {
      chart.data.labels.push(label);
      chart.data.datasets.forEach((dataset) => {
          dataset.data.push(data);
      });
      chart.update();
  }

  function removeData(chart) {
      chart.data.labels.pop();
      chart.data.datasets.forEach((dataset) => {
          dataset.data.pop();
      });
      chart.update();
  }

  function fetchData(parameter_name, callBack){
    $.get(url='ajax/get_stats', 
        data={'parameter_name': parameter_name}, 
        success=callBack, 
        dataType='json');
  }

  function fetchAllData(callBack){
    $.get(url='ajax/get_all_stats', 
        data={}, 
        success=function(responce){ callBack(responce.data); }, 
        dataType='json');
  }

  function runUpdateCycle(parameter_name, chart_obj){
      fetchData(parameter_name, function(responce){
        chart_obj.config.data.labels = responce.data.x.map(function(timeStr){ return moment.utc(timeStr).local().format('hh:mm:ss').toString(); });
//        chart_obj.data.labels = responce.data.x.map(function(timeStr){ return moment(timeStr).format('hh:mm:ss'); });
        chart_obj.data.datasets.forEach((dataset) => {
            dataset.data = responce.data.y;
        });
        chart_obj.update();
        setTimeout(runUpdateCycle, {{stats_update_timeout}}, parameter_name, chart_obj);
      });
  }