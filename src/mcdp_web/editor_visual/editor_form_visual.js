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

    if (diagram == null) {
        diagram = create_diagram(diagram_id, nodes, links);
    } else {
        diagram.startTransaction("update");

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

    var png = myDiagram.makeImage();
    console.log(png)
    console.log(png.html())
    var svg = myDiagram.makeSvg({
        // document: newDocument,  // create SVG DOM in new document context
        //     scale: 9,
        // maxSize: new go.Size(600, NaN)
    });
    console.log(svg);
    // svg_string = svg.toString()
    // console.log(svg_string)
}


function init_go_diagram() {
    nodes = [{"key": 2, "name": "unit Two", "loc": "320 152"}]
    links = [];
    // diagram = create_diagram(diagram_id, nodes, links);
}

$(document).ready(init_go_diagram);
