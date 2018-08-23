using_visual_editor = true;
ajax_parse_path = 'ajax_parse_visual';

var gojs_graph_json = JSON.parse({{gojs_graph_json | safe}});

var diagram_id = 'myDiagramDiv';
var diagram = null;

function update_diagram_after_successful_parse(res) {
    console.log('ok now time to do diagram');

    data = res['gojs'];
    console.log(data);
    nodes = data['nodes'];
    links = data['links'];

    if (diagram == null) {
        init_go_diagram();
    } else {

        diagram.startTransaction("update");

        console.log(nodes);
        key2nodes = new Map();
        for (i in nodes) {
            node = nodes[i];
            key = node['key'];
            console.log('need to have ' + key);
            key2nodes.set(key, node);

        }


        key2node_existing = new Map();
        keys_to_remove = new Map();
        myDiagram.nodes.each(function (n) {
            // if (n.data.text ... && n.data.key ...) { ... do something ... }
            key = n.data.key;
            console.log('existing node: ' + key);
            if (key2nodes.has(key)) {
                console.log('still exists');
            } else {
                console.log('need to remove ' + key);
                keys_to_remove.set(key, n.data);
            }
            key2node_existing.set(key, n.data);
        });

        for (var key of keys_to_remove.keys()) {
            console.log('removing ' + key);
            diagram.model.removeNodeData(keys_to_remove.get(key));
        }

        console.log(key2nodes);
        for (var key of key2nodes.keys()) {
            console.log('considering ' + key)
            if (!key2node_existing.has(key)) {
                console.log('need to add key ' + key);
                node_data = key2nodes.get(key);
                console.log(node_data);
                diagram.model.addNodeData(node_data);
            } else {
                console.log('already have key ' + key);

                new_data = key2nodes.get(key);
                old_data = key2node_existing.get(key);
                diagram.model.setDataProperty(old_data, 'rightArray', new_data['rightArray']);
                diagram.model.setDataProperty(old_data, 'leftArray', new_data['leftArray']);
            }
        }

        key2link_existing = new Map();
        myDiagram.links.each(function (l) {
            console.log('got link ' + l.data.key)
            key2link_existing.set(l.data.key, l.data);
        });
        console.log('key2link_existing', key2link_existing)

        key2links = new Map()
        for (link in links) {
            link_data = links[link];
            key = link_data['key'];
            console.log("need to have link " + key);
            key2links.set(key, link_data);
        }

        for (var key of key2link_existing.keys()) {
            console.log('I have key ' + key)
            if (!key2links.has(key)) {
                console.log('removing ' + key);
                diagram.model.removeLinkData(key2link_existing.get(key));
            }
        }

        for (var key of key2links.keys()) {
            if (!key2link_existing.has(key)) {
                console.log('adding ' + key);
                diagram.model.addLinkData(key2links.get(key));
            }
        }


        diagram.commitTransaction("update");
        console.log('Done diagram');
    }

    // var png = myDiagram.makeImage();
    // console.log(png)
    // console.log(png.html())
    // var svg = myDiagram.makeSvg({
    //     // document: newDocument,  // create SVG DOM in new document context
    //     //     scale: 9,
    //     // maxSize: new go.Size(600, NaN)
    // });
    // console.log(svg);
    // svg_string = svg.toString()
    // console.log(svg_string)


}


function init_go_diagram() {

    nodes = [{"key": 2, "name": "unit Two", "loc": "320 152"}]
    links = [];

    diagram = create_diagram(diagram_id, nodes, links);
    console.log(gojs_graph_json)
    if (gojs_graph_json != null)
        diagram.model = go.Model.fromJson(gojs_graph_json);

    // notice whenever a transaction or undo/redo has occurred
    diagram.addModelChangedListener(function (evt) {
        if (evt.isTransactionFinished) model_was_modified(evt.model);
    });
    // diagram.addDiagramEventListener(function (evt) {
    //     console.log()
    //     console.log(evt);
    // });
}

$(document).ready(init_go_diagram);


function model_was_modified(model) {
    json = diagram.model.toJson();
    save_gojs_json(json);
}


function save_gojs_json(json) {
    function on_proc_failure(res) {
        // $('#syntax_error').html(res['error']);
        // $('#syntax_error').show();
        // $('#language_warnings').html(); /* XXX */
        // $('#around_editor').css('background-color', bg_color_parsing);

        console.log(res['error']);
    }

    function on_success(res) {
        console.log('success');
    }

    ajax_send('save_gojs_graph', {'gojs_graph': json}, on_comm_failure, on_proc_failure, on_success);
}
