// load necessary scripts (add them to the <head> section)
// chaining them as everything loading after the page is ready will be done
// asynchronously, but some need others (d3-dag.js needs d3.js for one)
// could have done something with promises but it is currently past midnight and i have
// to work early tomorrow
const s = document.createElement("script");
s.src = "https://unpkg.com/d3";
s.onload = () => {
    console.log("Loaded d3.js");
    const s = document.createElement("script");
    s.src = "https://unpkg.com/d3-dag";
    s.onload = () => {
        console.log("Loaded d3-dag.js");
    }
    document.head.appendChild(s);
}
document.head.appendChild(s);

// fetch browser-calculated styling properties
const computedStyle = window.getComputedStyle(document.documentElement);

// https://observablehq.com/@d3/hierarchical-edge-bundling
// below are the default options for to render the circle
const generateGraph = (
    data,
    {
        nodeColor = "#000", // node color
        nodeRadius = 15, // node radius, in internal units
        linkColor = "#000", // link color
        linkColorIncoming = "#07f", // link color for parents
        linkColorOutgoing = "#f77", // link color for children
    } = {}
) => {

    // prepare the data according to d3-dag wishes
    const dag = d3.dagStratify()(data);

    // parameterise the layout options
    const layout = d3.sugiyama()
                     .layering(d3.layeringSimplex())
                     .decross(d3.decrossOpt())
                     .coord(d3.coordQuad())
                     .nodeSize(d => [3*nodeRadius, 6*nodeRadius]);

    // compute the layout based on the provided data
    const { width, height } = layout(dag);

    // generate a link between two nodes
    const computeLink = d3.line().curve(d3.curveCatmullRom).x(d => d.x).y(d => d.y);

    // svg canvas
    const svg = d3.create("svg")
      .attr("id", "depviz-graph")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height]);

    // build the nodes
    const nodes = svg.append("g")
      .selectAll("g")
      .data(dag.descendants())
      .enter()
      .append("g")
      .attr("transform", ({ x, y }) => `translate(${x}, ${y})`)

    nodes.append("circle")
      .attr("fill", nodeColor)
      .attr("r", nodeRadius);

    //nodes.append("text")
    //  .text(d => d.data.id)
    //  .attr("alignment-baseline", "middle")
    //  .attr("font-family", "sans-serif")
    //  .attr("text-anchor", "middle")
    //  .attr("fill", nodeColor);

    // build the links
    const lines = svg.append("g")
      .selectAll("path")
      .data(dag.links())
      .enter()
      .append("path")
      .attr("d", ({ points }) => computeLink(points))
      .attr("fill", "none")
      .attr("stroke", nodeColor)
      .attr("stroke-width", 1);

    return svg.node();

}

// process the posted data and draw the svg
const drawGraph = (data) => {

    // add the graph to the page
    document.getElementById("depviz").appendChild(
        generateGraph(
            data,
            {
                nodeColor: computedStyle.getPropertyValue("--font-color"),
                linkColor: computedStyle.getPropertyValue("--font-color"),
                linkColorIncoming: computedStyle.getPropertyValue("--link-color"),
                //width: window.innerWidth - 4*parseInt(computedStyle.fontSize), // does not account for scrollbar width
                //height: Math.max(window.innerHeight, 1200)
            }
        )
    );

}

// transform data into the expected format
const toJSON = (rawData, inputFormat, reverseTree) => {
    const data = [],
          nodes = [];

    let _data = {};

    // json input
    if (inputFormat === "json") {
        const jsonData = JSON.parse(rawData);

        // parent -> child[ren]
        if (reverseTree) {

            // build the json data
            Object.keys(jsonData).forEach(p => {
                if (!nodes.includes(p)) nodes.push(p);
                jsonData[p].forEach(c => {
                    if (!nodes.includes(c)) nodes.push(c);
                    if (Object.keys(_data).includes(c)) {
                        _data[c].push(p);
                    } else {
                        _data[c] = [p];
                    }
                });
            });
        }

        // child -> parent[s] (nothing to do)
        else {
            _data = jsonData;
        }

    }

    // csv input
    else {
        rawData.split("\n").forEach(l => {
            let c = "", // child
                p = ""; // parent

            // parent -> child[ren]
            if (reverseTree) {
                [p, c] = l.split(",").map(o => o.trim());
            }

            // child -> parent[s]
            else {
                [c, p] = l.split(",").map(o => o.trim());
            }

            // build the json data
            if (c && p && c.length && p.length) {
                if (!nodes.includes(c)) nodes.push(c);
                if (!nodes.includes(p)) nodes.push(p);
                if (Object.keys(_data).includes(c)) {
                    _data[c].push(p);
                } else {
                    _data[c] = [p];
                }
            }

        });
    }

    // object -> array of objects
    nodes.forEach(o => {
        if (Object.keys(_data).includes(o)) {
            data.push({"id": o, "parentIds": _data[o]});
        } else {
            data.push({"id": o, "parentIds": []});
        }
    });

    return data;
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

        // remove the circle
        document.getElementById("depviz-graph").remove();

        // reset the form
        document.getElementById("depviz-form").innerHTML = form;
        document.getElementById("depviz-button").innerHTML = "Submit";

    } else {

        // convert to input expected by the rendering function
        const data = toJSON(
            document.getElementById("depviz-raw").value,
            (document.getElementById("depviz-json").checked) ? "json" : "csv",
            (document.getElementById("depviz-reverse").checked) ? true : false
        );

        // remove the form
        document.getElementById("depviz-form").innerHTML = "";
        document.getElementById("depviz-button").innerHTML = "Reset";

        // draw the circle
        drawGraph(data);

    }
});
