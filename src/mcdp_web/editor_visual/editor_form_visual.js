
function diagram_update_success(res) {
    res_text = res['request']['text']
    relevant = still_relevant(res_text);

    if (!relevant || (res_text != last_text_sent_to_server)) {
        //console.log('Slow server: ignoring stale.');
        show_status('#server_status', 'Server is slow in responding...');
        return;
    }

    if (multiple_selection())
        return;

    image_set_text(res_text);

    string_with_suggestions = res['string_with_suggestions']
    if (null != string_with_suggestions) {
        if (string_with_suggestions != res_text) {
            $('#apply_suggestions').show();
        } else {
            $('#apply_suggestions').hide();
        }
    } else {
        $('#apply_suggestions').hide();
    }

    $('#around_editor').css('background-color', 'white');
    $('#syntax_error').hide();
    $('#syntax_error').html('');
    if ('language_warnings' in res) {
        $('#language_warnings').html(res['language_warnings']);
    }

    update_text_with_highlight(res_text, res['highlight']);
}

function diagram_update_failure(res) {
    // $('#syntax_error').html(res['error']);
    // $('#syntax_error').show();
    // $('#language_warnings').html();
    // /* XXX */
    // $('#around_editor').css('background-color', bg_color_parsing);
    //
    // if ('highlight' in res) {
    //     res_text = res['request']['text']
    //     relevant = still_relevant(res_text);
    //     //console.log('relevant ' +relevant)
    //     if (relevant)
    //         update_text_with_highlight(res_text, res['highlight']);
    //     else {
    //         show_status('#server_status', 'Server is slow in responding...');
    //     }
    // }
}

function diagram_update(s) {
    last_text_sent_to_server = s;
    ajax_send("ajax_parse", {'text': s},
        on_comm_failure, diagram_update_failure, diagram_update_success);
}

function init_go_diagram() {

    nodes = [

        {
            key: 1, group: 0, "name": "unit One", "loc": "101 204",
            "leftArray": [
                {
                    "portId": "F0",
                    "port_label": "F0 [m]",
                    "unit": "m",
                }
            ],

            "rightArray": [
                {
                    "portId": "R0",
                    "port_label": "R0 [W]",
                    "unit": "W",
                },
                {

                    "portId": "R1",
                    "port_label": "R1 [m]",
                    "unit": "m",
                }]
        },
        {
            group: 0,
            "key": 2, "name": "unit Two", "loc": "320 152",
            "leftArray": [
                {
                    "unit": "m",
                    "portId": "F0",
                    "port_label": "F0 [m]",
                }, {
                    "portId": "F1",
                    "port_label": "F1 [W]",
                    "unit": "W",
                }, {
                    "portId": "F2",
                    "port_label": "F2 [s]",
                    "unit": "s",
                }],

            "rightArray": [{
                "portId": "R2",
                "port_label": "R2 [m]",
                "unit": "m",
            }]
        },
        {
            group: 0,
            "key": 3, "name": "unit Three", "loc": "384 319",
            "leftArray": [
                {
                    "portId": "F0",
                    "port_label": "F0 [m]",
                    "unit": "m",
                },
                {
                    "portId": "F1",
                    "port_label": "F1 [m]",
                    "unit": "m",
                },
                {
                    "portId": "F3",
                    "port_label": "F3 [Bool]",
                    "unit": "Bool",
                },
            ],
            "rightArray": []
        },
        {
            group: 0,
            "key": 4, "name": "unit Four", "loc": "138 351",
            "leftArray": [{
                "portId": "F0",
                "port_label": "F0 [m]",
                "unit": "m",
            }],

            source: "https://placebear.com/128/128",

            "rightArray": [
                {
                    "portId": "R1",
                    "port_label": "R1 [Bool]",
                    "unit": "Bool"
                },
                {
                    "portId": "R2",
                    "port_label": "R2 [s]",
                    "unit": "s",
                }]
        },
        {
            group: 0,
            category: "f_template",
            "key": "f", "name": "f", "loc": "138 351",
            location: new go.Point(-200, 100),
            "rightArray": [
                {
                    "portId": "R2",
                    "port_label": "R2 [s]",
                    "unit": "s",
                }]
        },
        {
            group: 0,
            category: "f_template",
            "key": "f", "name": "f", "loc": "138 351",
            location: new go.Point(-200, -100),
            "rightArray": [
                {
                    "portId": "R2",
                    "port_label": "another",
                    "unit": "s",
                }],


        }
    ]
    links = []

    myDiagram = create_diagram(nodes, links);
}

$(document).ready(init_go_diagram);
