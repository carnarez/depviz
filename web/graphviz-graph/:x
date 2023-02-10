import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@9/dist/mermaid.esm.min.mjs";

// fetch browser-calculated styling properties
const computedStyle = window.getComputedStyle(document.documentElement);

// see https://mermaid.live/ for examples
// https://mermaid.js.org/config/usage.html#api-usage
const generateMermaidDiagram = (
    data,
    {
        diagramOrientation = "TB", // diagram orientation
        fontColor = "#000", // font color
        nodeColor = "#fff", // node background color
        nodeBorderColor = "#000", // node border color
        linkColor = "#000" // link color
    } = {}
) => {

    // configure mermaid: only modify the minimal color choice
    mermaid.mermaidAPI.initialize({
        startOnLoad: false,
        theme: "base",
        themeVariables: {
            fontFamily: computedStyle.getPropertyValue("--font-family"),
            fontSize: computedStyle.getPropertyValue("--font-size"),
            primaryColor: nodeColor,
            primaryBorderColor: nodeBorderColor,
            primaryTextColor: fontColor,
            lineColor: linkColor
        }
    });

    // build the list of unique nodes
    const nodes = {};
    let i = 0;
    Object.keys(data).forEach(n1 => {
        if (!Object.keys(nodes).includes(n1)) {
            i += 1;
            nodes[n1] = i;
        }
        data[n1].forEach(n2 => {
            if (!Object.keys(nodes).includes(n2)) {
                i += 1;
                nodes[n2] = i;
            }
        });
    });

    // diagram in mermaid syntax
    let diagram = `graph ${diagramOrientation}\n`;

    // nodes
    diagram += "  %% nodes\n";
    Object.keys(nodes).forEach(n => diagram += `  node${nodes[n]}(${n})\n`);

    // links
    diagram += "  %% links\n";
    Object.keys(data).forEach(n1 => {
        data[n1].forEach(n2 => {
            diagram += `  node${nodes[n1]} --- node${nodes[n2]}\n`;
        });
    });

    // style (another way to show styling mermaid is cumbersome)
    diagram += "  %% style\n";
    diagram += `  linkStyle default stroke-width:1px;\n`;

    // debug
    console.log(diagram);

    // html element that will carry the diagram
    const element = document.createElement("svg");
    element.id = "depviz-graph";

    // add the diagram to the element
    mermaid.mermaidAPI.render(
        "mermaid-diagram", diagram, (svg) => { element.innerHTML = svg; }
    );

    return element;
}

// process the posted data and draw the svg
const drawGraph = (data, orientation) => {

    // add the graph to the page
    document.getElementById("depviz").appendChild(
        generateMermaidDiagram(
            data,
            {
                diagramOrientation: orientation,
                fontColor: computedStyle.getPropertyValue("--font-color"),
                nodeColor: computedStyle.getPropertyValue("--background-color-alt"),
                nodeBorderColor: computedStyle.getPropertyValue("--font-color"),
                linkColor: computedStyle.getPropertyValue("--font-color")
            }
        )
    );

}

// transform data into the expected format
// this one requires a child -> parents flow
const toJSON = (rawData, inputFormat, reverseTree) => {
    const data = {};

    // json input
    if (inputFormat === "json") {
        const jsonData = JSON.parse(rawData);

        // child -> parent[s]
        if (reverseTree) {
            return jsonData;
        }

        // parent -> child[ren] (nothing to do)
        else {

            // build the json data
            Object.keys(jsonData).forEach(c => {
                jsonData[c].forEach(p => {
                    if (Object.keys(data).includes(p)) {
                        data[p].push(c);
                    } else {
                        data[p] = [c];
                    }
                });
            });

        }

    }

    // csv input
    else {
        rawData.split("\n").forEach(l => {
            let c = "", // child
                p = ""; // parent

            // child -> parent[s]
            if (reverseTree) {
                [c, p] = l.split(",").map(o => o.trim());
            }

            // parent -> child[ren]
            else {
                [p, c] = l.split(",").map(o => o.trim());
            }

            // build the json data
            if (c && p && c.length && p.length) {
                if (Object.keys(data).includes(c)) {
                    data[c].push(p);
                } else {
                    data[c] = [p];
                }
            }

        });
    }

    if (Object.keys(data).length === 0) {
        throw "InputError";
    } else {
        return data;
    }
}

// define the form elements
const form = `
<textarea
  id="depviz-raw"
  placeholder="select input format and whether a list of parents per child or a list of children per parent is provided"
  rows="3"
></textarea>
<input id="depviz-csv" name="format" type="radio" checked>
<label for="depviz-csv">CSV</label>
<input id="depviz-json" name="format" type="radio">
<label for="depviz-json">JSON</label>
<input id="depviz-reverse" name="flow" type="radio" checked>
<label for="depviz-reverse">parent &rarr; children</label>
<input id="depviz-vanilla" name="flow" type="radio">
<label for="depviz-vanilla">child &rarr; parents</label>
<input id="depviz-lr" name="orientation" type="radio" value="LR">
<label for="depviz-lr"></label>
<input id="depviz-tb" name="orientation" type="radio" value="TB" checked>
<label for="depviz-tb"></label>
<input id="depviz-rl" name="orientation" type="radio" value="RL">
<label for="depviz-rl"></label>
<input id="depviz-bt" name="orientation" type="radio" value="BT">
<label for="depviz-bt"></label>
`;

// add the initial form to the page
document.getElementById("depviz").innerHTML += `
<div id="depviz-form">${form}</div>
<div class="depviz-buttons">
  <a id="depviz-button">Submit</a>
</div>
`;

// event listener
document.getElementById("depviz-button").addEventListener("click", (event) => {
    if (document.getElementById("depviz-graph")) {

        // remove the diagram
        document.getElementById("depviz-graph").remove();

        // reset the form
        document.getElementById("depviz-form").innerHTML = form;
        document.getElementById("depviz-button").innerHTML = "Submit";

    } else {
        try {

            // convert to input expected by the rendering function
            const data = toJSON(
                document.getElementById("depviz-raw").value,
                (document.getElementById("depviz-json").checked) ? "json" : "csv",
                (document.getElementById("depviz-reverse").checked) ? true : false
            );

            // draw the diagram
            drawGraph(
                data,
                document.querySelector('input[name="orientation"]:checked').value
            );

            // remove the form
            document.getElementById("depviz-form").innerHTML = "";
            document.getElementById("depviz-button").innerHTML = "Reset";

        } catch(e) {

            // highlight the textarea
            document.getElementById("depviz-raw").classList.add("error");

        }
    }
});
