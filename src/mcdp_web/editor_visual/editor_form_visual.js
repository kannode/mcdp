using_visual_editor = true;
ajax_parse_path = 'ajax_parse_visual';

var diagram_id = 'myDiagramDiv';
var diagram = null;

function update_diagram_after_successful_parse(res) {
    console.log('ok now time to do diagram');

    data = res['gojs'];
    console.log(data);
    nodes = data['nodes'];
    links = data['links'];

    diagram.startTransaction("update");

    // model2 = diagram.model.copy()

    diagram.model.removeNodeDataCollection(diagram.model.nodeDataArray);
    for (node in nodes) {
        console.log("adding node");
        node_data = nodes[node];
        console.log(node_data);
        diagram.model.addNodeData(node_data);
    }

    diagram.model.removeLinkDataCollection(diagram.model.linkDataArray);

    for (link in links) {
        console.log("adding link");
        link_data = links[link];
        console.log(link_data);
        diagram.model.addLinkData(link_data);
    }

    diagram.commitTransaction("update");
    console.log('Done diagram');
}


function init_go_diagram() {
    nodes = [{"key": 2, "name": "unit Two", "loc": "320 152"}]
    links = [];
    diagram = create_diagram(diagram_id, nodes, links);
}

$(document).ready(init_go_diagram);


//
// nodes = [
//
//     {
//         key: 1, group: 0, "name": "unit One", "loc": "101 204",
//         "leftArray": [
//             {
//                 "portId": "F0",
//                 "port_label": "F0 [m]",
//                 "unit": "m",
//             }
//         ],
//
//         "rightArray": [
//             {
//                 "portId": "R0",
//                 "port_label": "R0 [W]",
//                 "unit": "W",
//             },
//             {
//
//                 "portId": "R1",
//                 "port_label": "R1 [m]",
//                 "unit": "m",
//             }]
//     },
//     {
//         group: 0,
//         "key": 2, "name": "unit Two", "loc": "320 152",
//         "leftArray": [
//             {
//                 "unit": "m",
//                 "portId": "F0",
//                 "port_label": "F0 [m]",
//             }, {
//                 "portId": "F1",
//                 "port_label": "F1 [W]",
//                 "unit": "W",
//             }, {
//                 "portId": "F2",
//                 "port_label": "F2 [s]",
//                 "unit": "s",
//             }],
//
//         "rightArray": [{
//             "portId": "R2",
//             "port_label": "R2 [m]",
//             "unit": "m",
//         }]
//     },
//     {
//         group: 0,
//         "key": 3, "name": "unit Three", "loc": "384 319",
//         "leftArray": [
//             {
//                 "portId": "F0",
//                 "port_label": "F0 [m]",
//                 "unit": "m",
//             },
//             {
//                 "portId": "F1",
//                 "port_label": "F1 [m]",
//                 "unit": "m",
//             },
//             {
//                 "portId": "F3",
//                 "port_label": "F3 [Bool]",
//                 "unit": "Bool",
//             },
//         ],
//         "rightArray": []
//     },
//     {
//         group: 0,
//         "key": 4, "name": "unit Four", "loc": "138 351",
//         "leftArray": [{
//             "portId": "F0",
//             "port_label": "F0 [m]",
//             "unit": "m",
//         }],
//
//         source: "https://placebear.com/128/128",
//
//         "rightArray": [
//             {
//                 "portId": "R1",
//                 "port_label": "R1 [Bool]",
//                 "unit": "Bool"
//             },
//             {
//                 "portId": "R2",
//                 "port_label": "R2 [s]",
//                 "unit": "s",
//             }]
//     },
//     {
//         group: 0,
//         category: "f_template",
//         "key": "f", "name": "f", "loc": "138 351",
//         location: new go.Point(-200, 100),
//         "rightArray": [
//             {
//                 "portId": "R2",
//                 "port_label": "R2 [s]",
//                 "unit": "s",
//             }]
//     },
//     {
//         group: 0,
//         category: "f_template",
//         "key": "f", "name": "f", "loc": "138 351",
//         location: new go.Point(-200, -100),
//         "rightArray": [
//             {
//                 "portId": "R2",
//                 "port_label": "another",
//                 "unit": "s",
//             }],
//
//
//     }
// ]
