var DARK_RED = '#800400';
var DARK_GREEN = '#096e19';

function create_diagram(diagram_id, nodes, links) {
    var $ = go.GraphObject.make;

    myDiagram =
        $(go.Diagram, diagram_id, // the ID of the DIV HTML element
            {
                initialContentAlignment: go.Spot.Center,
                // layout: $(go.ForceDirectedLayout),
                "undoManager.isEnabled": true
            });
    //
    // regular_template =
    //     $(go.Node, go.Panel.Auto,
    //         {locationSpot: go.Spot.Center},
    //         new go.Binding("location", "location").makeTwoWay(),
    //         $(go.Shape,
    //             {
    //                 figure: "RoundedRectangle",
    //                 parameter1: 10,
    //                 fill: "orange",  // default fill color
    //                 portId: "",
    //                 fromLinkable: true,
    //                 fromSpot: go.Spot.AllSides,
    //                 toLinkable: true,
    //                 toSpot: go.Spot.AllSides,
    //                 cursor: "pointer"
    //             },
    //             new go.Binding("fill", "color")),
    //         $(go.TextBlock,
    //             {margin: 10, font: "bold 12pt sans-serif"},
    //             new go.Binding("text"))
    //     );

    function MultiColoredLink() {

        go.Link.call(this);

    }

    go.Diagram.inherit(MultiColoredLink, go.Link);


    MultiColoredLink.prototype.makeGeometry = function () {
        var geo = go.Link.prototype.makeGeometry.call(this);
        var colors = [DARK_RED, DARK_GREEN];

        var paths = [];  // find all path Shapes

        this.elements.each(function (elt) {
            if (elt.isPanelMain && elt instanceof go.Shape) {
                paths.push(elt);
            }
        });

        var numcolors = Math.min(colors.length, paths.length);

        if (numcolors > 0) {

            var seclen = geo.flattenedTotalLength / numcolors;  // length of each color section

            for (var i = 0; i < paths.length; i++) {  // go through all path Shapes
                var shape = paths[i];
                if (i < numcolors) {
                    shape.visible = true;  // make sure this Shape can be seen
                    shape.stroke = colors[i];  // and assign a color

                    if (i > 0) {  // and a stroke dash array so that it only draws the needed fraction
                        shape.strokeDashArray = [0, i * seclen, seclen, 99999];
                    }

                    // shape.toArrow = "Standard"
                    // shape.fromArrow = "Standard"

                } else {  // unneeded Shapes are not visible
                    shape.visible = false;
                }
            }
        }

        return geo;

    }

    var portSize = new go.Size(8, 8);

    function delete_component(e, obj) {
        myDiagram.startTransaction("delete_component");
        // get the context menu that holds the button that was clicked
        var contextmenu = obj.part;
        // get the node data to which the Node is data bound
        myDiagram.remove(obj);
        myDiagram.commitTransaction("delete_component");
    }

    contextMenu = $(go.Adornment, "Vertical",  // that has one button
        $("ContextMenuButton", $(go.TextBlock, "Delete"), {click: delete_component}),

        // more ContextMenuButtons would go here
    );  // end Adornment

    link_properties = {
        relinkableFrom: true,
        relinkableTo: true,
        reshapable: true,
        resegmentable: true,
        fromEndSegmentLength: 10,
        toEndSegmentLength: 10,

        routing: go.Link.AvoidsNodes,
        corner: 10,
        curve: go.Link.JumpOver,

    };

    regular_link =

        $(MultiColoredLink,
            link_properties,
            new go.Binding("points").makeTwoWay(),
            $(go.Shape, {isPanelMain: true, strokeWidth: 2, strokeDashArray: [3, 3]}),
            $(go.Shape, {isPanelMain: true, strokeWidth: 2}),
            $(go.Shape, "Circle", {width: 10, height: 10, fill: "white", strokeWidth: 1.5})
        );

    f_link =
        $(go.Link,
            link_properties,
            new go.Binding("points").makeTwoWay(),
            $(go.Shape, {isPanelMain: true, strokeWidth: 2, stroke: DARK_GREEN}),
        );


    r_link =
        $(go.Link,
            link_properties,
            new go.Binding("points").makeTwoWay(),
            $(go.Shape, {isPanelMain: true, strokeWidth: 2, stroke: DARK_RED, strokeDashArray: [3, 3]}),
        );


    LEFT = $(go.Panel, "Vertical",
        new go.Binding("itemArray", "leftArray"),
        {
            row: 1, column: 0,
            itemTemplate:
                $(go.Panel,
                    {
                        _side: "left",  // internal property to make it easier to tell which side it's on
                        fromSpot: go.Spot.Left, toSpot: go.Spot.Left,
                        fromLinkableSelfNode: false, toLinkableSelfNode: true,
                        fromLinkable: false, toLinkable: true, cursor: "pointer",
                        // contextMenu: portMenu
                    },
                    new go.Binding("portId", "portId"),
                    $(go.TextBlock, {
                            stroke: DARK_GREEN,
                            textAlign: "right"
                        },
                        new go.Binding("text", "port_label")),
                )
        }
    );
    RIGHT = $(go.Panel, "Vertical",
        new go.Binding("itemArray", "rightArray"),
        {
            row: 1,
            column: 2,
            itemTemplate:
                $(go.Panel,
                    {
                        _side: "right",
                        fromSpot: go.Spot.Right,
                        toSpot: go.Spot.Right,
                        fromLinkableSelfNode: true, toLinkableSelfNode: false,
                        fromLinkable: true, toLinkable: false, cursor: "pointer",
                        // contextMenu: portMenu
                    },
                    new go.Binding("portId", "portId"),
                    $(go.TextBlock, {
                        stroke: DARK_RED,
                        textAlign: "right"
                    }, new go.Binding("text", "port_label")),
                )  // end itemTemplate
        }
    );

    text_properties = {
        margin: 5,
        editable: true,
        // padding: 10,
        textAlign: "center",
        font: "14px  Times",
        stroke: "black",
        row: 0,
        column: 1,
    };

    TEXT = $(go.TextBlock, text_properties,
        new go.Binding("text", "name"));

    PIC = $(go.Picture, {
            row: 1,
            column: 1,

        },
        new go.Binding("source", "source")
    )

    TABLE = $(go.Panel, "Table", TEXT, LEFT, PIC, RIGHT);
    component_template = $(go.Node, "Auto",
        new go.Binding("location", "location").makeTwoWay(),
        $(go.Shape, "RoundedRectangle",
            {
                fill: "white", stroke: "black", strokeWidth: 2,
                minSize: new go.Size(56, 32),
            }),
        TABLE
    );

    t_template_text = $(go.TextBlock,
        {
            margin: 10,
            textAlign: "right",
            font: "14px  Times",
            stroke: DARK_GREEN,
            editable: true,
        },
        new go.Binding("text", "name").makeTwoWay())

    f_template =
        $(go.Node, "Auto", {},
            new go.Binding("location", "location").makeTwoWay(),
            $(go.Shape, "RoundedRectangle",
                {
                    fill: "#d0ffdc", stroke: "black", strokeWidth: 0,
                    minSize: new go.Size(56, 32),
                },
            ),
            $(go.Panel, "Vertical",
                new go.Binding("itemArray", "rightArray"),
                {
                    row: 1,
                    column: 2,
                    itemTemplate:
                        $(go.Panel,
                            {
                                _side: "left",
                                fromSpot: go.Spot.Right,
                                toSpot: go.Spot.Right,
                                fromLinkableSelfNode: true, toLinkableSelfNode: false,
                                fromLinkable: true, toLinkable: false, cursor: "pointer",
                                contextMenu: contextMenu
                            },
                            new go.Binding("portId", "portId"),
                            $(go.TextBlock, {
                                stroke: DARK_GREEN,
                                textAlign: "right"
                            }, new go.Binding("text", "port_label")),
                        )  // end itemTemplate
                }
            )
        );

    special =
        $(go.Node, "Auto", {},
            new go.Binding("location", "location").makeTwoWay(),
            $(go.Picture, {
                    maxSize: new go.Size(32, 32)
                },
                new go.Binding("source", "source")
            )
        );

    simple =
        $(go.Node, "Auto", {},
            new go.Binding("location", "location").makeTwoWay(),
            $(go.Shape, "RoundedRectangle",
                {
                    fill: "white", stroke: "black", strokeWidth: 2,
                    minSize: new go.Size(56, 32),
                },
            ),
            $(go.TextBlock, text_properties,
                new go.Binding("text", "name")));

    r_template =
        $(go.Node, "Auto", {},
            new go.Binding("location", "location").makeTwoWay(),
            $(go.Shape, "RoundedRectangle",
                {
                    fill: "#ffe6d7", stroke: "black", strokeWidth: 0,
                    minSize: new go.Size(56, 32)
                },
            ),
            $(go.Panel, "Vertical",
                new go.Binding("itemArray", "rightArray"),
                {
                    row: 1,
                    column: 0,
                    itemTemplate:
                        $(go.Panel,
                            {
                                _side: "left",
                                fromSpot: go.Spot.Left,
                                toSpot: go.Spot.Left,
                                fromLinkableSelfNode: false, toLinkableSelfNode: true,
                                fromLinkable: false, toLinkable: true, cursor: "pointer",
                                contextMenu: contextMenu
                            },
                            new go.Binding("portId", "portId"),
                            $(go.TextBlock, {
                                stroke: DARK_RED,
                                textAlign: "left"
                            }, new go.Binding("text", "port_label")),
                        )  // end itemTemplate
                }
            )
        );

    function sameColor(fromnode, fromport, tonode, toport) {
        return fromport.data.unit === toport.data.unit;
    }

// only allow new links between ports of the same color
    myDiagram.toolManager.linkingTool.linkValidation = sameColor;

// only allow reconnecting an existing link to a port of the same color
    myDiagram.toolManager.relinkingTool.linkValidation = sameColor;


// create the nodeTemplateMap, holding three node templates:
    var templmap = new go.Map("string", go.Node);
    templmap.add("", component_template);
    templmap.add("f_template", f_template);
    templmap.add("r_template", r_template);
    templmap.add("special", special);
    templmap.add("simple", simple);
    myDiagram.nodeTemplateMap = templmap;

    var link_template_map = new go.Map("string", go.Link);
    link_template_map.add("", regular_link);
    link_template_map.add("f_link", f_link);
    link_template_map.add("r_link", r_link);
    myDiagram.linkTemplateMap = link_template_map;

// group_template_map = new go.Map("string", go.Node);
// group_template_map.add("", group_template);
// myDiagram.groupTemplateMap = group_template_map;

    myDiagram.model = $(go.GraphLinksModel, {
        linkFromPortIdProperty: "fromPort",
        linkToPortIdProperty: "toPort",
        nodeDataArray: nodes,
        linkDataArray: links,
        linkKeyProperty: 'key',
    });

    return myDiagram;
}
