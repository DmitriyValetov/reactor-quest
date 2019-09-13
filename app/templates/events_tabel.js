$(document).ready(function() {
    var events_table = $('#events_table');

    function fetchData(callBack){
        $.get(url='ajax/get_events', 
            data={}, 
            success=callBack, 
            dataType='json');
    }

    function post_process_stop_request(responce){
        var obj = JSON.parse(responce);
        console.log(obj);        
        if(obj.hasOwnProperty('event_id')){
            $(`tr #${obj.id}`).remove();
        }
    }

    function try_to_stop_event(){
        var event_id = Number($(this).attr('id'));
        $.get('ajax/stop_event', {'event_id': event_id}, post_process_stop_request)
    }

    function build_events_table(events_cur_step){
        var events = events_cur_step.events,
            cur_step = events_cur_step.cur_step;
        events_table.empty();
        events.forEach(function(event_obj){
            if(event_obj.access){
                events_table.append(`
                    <tr id='${event_obj['id']}'>
                    <td>${event_obj['view_name']}</td>
                    <td>${event_obj['view_source']}</td>
                    <td>${event_obj['end']-cur_step}</td>
                    <td><button id="${event_obj['id']}" class='btn btn-secondary'><i class="fa fa-times" aria-hidden="true"></i></button></td>
                    </tr>
                `);

                // bind delete action
                $(`#events_table #${event_obj['id']}`).on('click', try_to_stop_event);

            } else {
                events_table.append(`
                    <tr>
                        <td>${event_obj['view_name']}</td>
                        <td>${event_obj['view_source']}</td>
                        <td></td>
                    </tr>
                `);
            }
        });
    }


    function run_events_table(){
        fetchData(function(events_cur_step){
            /**
             * event: id, name, source, status(1)
             */
            build_events_table(events_cur_step);
            setTimeout(run_events_table, {{stats_update_timeout}});     
        });
    }

    run_events_table();


});