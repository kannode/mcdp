function init() {

    var GM = go.GraphObject.make;

    myDiagram = GM(go.Diagram, "myDiagramDiv");

    //
    //
    // // define a simple Node template
    // myDiagram.nodeTemplate =
    //     $(go.Node, "Auto",  // the Shape will go around the TextBlock
    //         $(go.Shape, "RoundedRectangle", {strokeWidth: 0},
    //             // Shape.fill is bound to Node.data.color
    //             new go.Binding("fill", "color")),
    //         $(go.TextBlock,
    //             {margin: 8},  // some room around the text
    //             // TextBlock.text is bound to Node.data.key
    //             new go.Binding("text", "key"))
    //     );

    // but use the default Link template, by not setting Diagram.linkTemplate

    // create the model data that will be represented by Nodes and Links
    myDiagram.model = new go.GraphLinksModel();

    myDiagram.model.nodeDataArray = [
        {key: "Alpha", color: "lightblue"},
        {key: "Beta", color: "orange"},
        {key: "Gamma", color: "lightgreen"},
        {key: "Delta", color: "pink", group: "G1"},
        {key: "G1", isGroup: true}
    ];

    myDiagram.model.linkDataArray = [
        {from: "Alpha", to: "Beta"},
        {from: "Alpha", to: "Gamma"},
        {from: "Delta", to: "G1"},
        {from: "Gamma", to: "Delta"},
        {from: "Delta", to: "Alpha"}
    ];

    S1 = GM(go.Shape, "RoundedRectangle", {fill: "white"});
    T1 = GM(go.TextBlock, "some text");
    myDiagram.add(GM(go.Part, "Position", S1, T1));
}
