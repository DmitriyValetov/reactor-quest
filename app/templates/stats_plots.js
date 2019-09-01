window.onload = function() {
    // var parameters_to_load = [
    //   'state',
    //   'rate',
    //   'acc',
    //   'produced'
    // ]
    // parameters_to_load.forEach(buildChart);
    fetchAllData(buildAllReceived);
};

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
          chart_holder[stat_name].data.datasets.forEach((dataset) => {
          dataset.data = responce.time_series[stat_name].y;
          chart_holder[stat_name].update();
        });
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
      var stats_data = data.time_series[stat_name];

      var container = document.getElementById('forCharts');
      var div = document.createElement('div');
      div.classList.add('chart-container');

      var canvas = document.createElement('canvas');
      canvas.setAttribute('id', 'canvas_'+stat_name);
      div.appendChild(canvas);
      container.prepend(div);

      var ctx = canvas.getContext('2d');
      var config = createConfig(stat_name, stats_data);
      var chart_obj = new Chart(ctx, config);
      chart_holder[stat_name] = chart_obj;
    });

    setTimeout(UpdateAllCharts, {{stats_update_timeout}}, chart_holder);
  }

  function createConfig(title, data) {
      return {
        type: 'line',
        data: {
          labels: data.x,
          datasets: [{
            // label: 'dataset label',
            steppedLine: false,
            data: data.y, 
            borderColor: window.chartColors.red,
            fill: false,
          }]
        },
        options: {
          legend: {
            display: false
          },
          responsive: true,
          title: {
            display: true,
            text: title,
          }
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
        chart_obj.data.datasets.forEach((dataset) => {
            dataset.data = responce.data.y;
        });
        chart_obj.update();
        setTimeout(runUpdateCycle, {{stats_update_timeout}}, parameter_name, chart_obj);
      });
    }

  function buildChart(parameter_name) {
    
    // var data = {
    //   'x':[
    //       1,2,3,4,5,6
    //     ],
    //   'y':[
    //       randomScalingFactor(),
    //       randomScalingFactor(),
    //       randomScalingFactor(),
    //       randomScalingFactor(),
    //       randomScalingFactor(),
    //       randomScalingFactor()
    //     ]
    // };
    var container = document.getElementById('forCharts');
    var div = document.createElement('div');
    div.classList.add('chart-container');

    var canvas = document.createElement('canvas');
    canvas.setAttribute('id', 'canvas_'+parameter_name);
    div.appendChild(canvas);
    container.prepend(div);

    var ctx = canvas.getContext('2d');
    fetchData(parameter_name, function(responce){
      var config = createConfig(parameter_name, responce.data);
      var chart_obj = new Chart(ctx, config);
      setTimeout(runUpdateCycle, {{stats_update_timeout}}, parameter_name, chart_obj);
    });

};