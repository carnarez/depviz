import * as d3 from "https://cdn.skypack.dev/d3@7";

// fetch browser-calculated styling properties
const computedStyle = window.getComputedStyle(document.documentElement);

// https://observablehq.com/@d3/hierarchical-edge-bundling
// below are the default options for to render the circle
const generateGraph = (
    data,
    {
        nodeColor = "#000", // node color
        linkColor = "#000", // link color
        linkColorIncoming = "#07f", // link color for parents
        linkColorOutgoing = "#f77", // link color for children
        radius = 200, // radius of the circle
        width = 800, // outer width, in pixels
        height = 800 // outer height, in pixels
    } = {}
) => {

    const dataT = {},
          nodes = {};

    // transpose the data to have a reversed index accessible quickly dependening on the
    // volume of data this can become expensive...
    Object.keys(data).forEach(n1 => {
        data[n1].forEach(n2 => {
            if (Object.keys(dataT).includes(n2)) {
                dataT[n2].push(n1);
            } else {
                dataT[n2] = [n1];
            }
        });
    });

    // build the list of unique nodes
    Object.keys(data).forEach(n1 => {
        if (!Object.keys(nodes).includes(n1)) nodes[n1] = {"name": n1};
        data[n1].forEach(n2 => {
            if (!Object.keys(nodes).includes(n2)) nodes[n2] = {"name": n2}
        });
    });

    // sorted list of nodes
    const sorted = Object.keys(nodes).sort();

    // scale the radius
    if (nodes.length > 100) radius *= 2;

    // computed angle between two nodes
    const angle = 2 * Math.PI / sorted.length;

    // scale the font size
    const fontSize = Math.min(
        2 * Math.sin(angle / 2) * radius,
        parseInt(computedStyle.fontSize)
    );

    // compute node properties
    // requires to calculate all of them before generating the list of linked nodes
    sorted.forEach((n, i) => {
        const a = i * angle - Math.PI / 2;
        nodes[n] = {
            "name": n,
            "objectId": n.replaceAll(".", "-"),
            "angle": a * 180 / Math.PI, // degrees
            "x": Math.cos(a) * radius, // scaled to radius
            "y": Math.sin(a) * radius, // scaled to radius
            "_angle": a, // radians
            "_x": Math.cos(a), // unit circle
            "_y": Math.sin(a), // unit circle
            "incoming": [],
            "outgoing": []
        };
    });

    // generate a link between two nodes
    // line curves around the centre of the circle
    const computeLink = (source, target) => {
        const line = d3.line().curve(d3.curveBundle.beta(0.85));
        return line([[source.x, source.y], [0, 0], [target.x, target.y]]);
    }

    // generate the list of nodes to be linked
    sorted.forEach(source => {
        const n1 = nodes[source];

        // incoming
        if (Object.keys(data).includes(source)) {
            data[source].forEach(target => {
                const n2 = nodes[target];
                n1.incoming.push({
                    "sourceId": n1.objectId,
                    "targetId": n2.objectId,
                    "path": computeLink(nodes[n1.name], nodes[n2.name])
                });
            });
        }

        // outgoing
        if (Object.keys(dataT).includes(source)) {
            dataT[source].forEach(target => {
                const n2 = nodes[target];
                n1.outgoing.push({
                    "sourceId": n2.objectId,
                    "targetId": n1.objectId,
                    "path": computeLink(nodes[n1.name], nodes[n2.name])
                });
            });

        }

    });

    // this function is called when a node is clicked; usefull for debug mainly
    const clicked = (e, d) => { console.log(d); }

    // this function is called when the mouse hovers an object and will highlight the
    // latter, but also the immediate parents/children of the object
    const overed = (e, d) => {
      d3.select(`#node-${d.objectId}`)
        .attr("font-size", "normal")
        .attr("font-weight", "bold")
        .raise();

      // links
      d.incoming.map(d => {
        d3.select(`#link-${d.sourceId}-${d.targetId}`)
          .attr("opacity", "1.0")
          .attr("stroke", linkColorIncoming)
          .attr("stroke-width", "3")
          .select(function() { return this.parentNode; })
          .raise();
      });
      d.outgoing.map(d => {
        d3.select(`#link-${d.sourceId}-${d.targetId}`)
          .attr("opacity", "1.0")
          .attr("stroke", linkColorOutgoing)
          .attr("stroke-width", "3")
          .select(function() { return this.parentNode; })
          .raise();
      });

      // nodes
      d.incoming.map(d => {
        d3.select(`#node-${d.targetId}`)
          .attr("fill", linkColorIncoming)
          .attr("font-size", "normal")
          .attr("font-weight", "bold")
          .raise();
      });
      d.outgoing.map(d => {
        d3.select(`#node-${d.sourceId}`)
          .attr("fill", linkColorOutgoing)
          .attr("font-size", "normal")
          .attr("font-weight", "bold")
          .raise();
      });

    }

    // this function is called when the mouse hovers *out* of an object, cleaning up all
    // the highlights; links seem to be capricious, so we make sure *all* related links
    // are back to normal
    const outed = (e, d) => {
      d3.select(`#node-${d.objectId}`)
        .attr("font-size", fontSize)
        .attr("font-weight", "normal");

      // links
      d.incoming.map(d => {
        d3.selectAll(`.from-${d.sourceId}`)
          .attr("opacity", "0.5")
          .attr("stroke", linkColor)
          .attr("stroke-width", "1");
      });
      d.outgoing.map(d => {
        d3.selectAll(`.from-${d.sourceId}`)
          .attr("opacity", "0.5")
          .attr("stroke", linkColor)
          .attr("stroke-width", "1");
      });

      // nodes
      d.incoming.map(d => {
        d3.select(`#node-${d.targetId}`)
          .attr("fill", nodeColor)
          .attr("font-size", fontSize)
          .attr("font-weight", "normal");
      });
      d.outgoing.map(d => {
        d3.select(`#node-${d.sourceId}`)
          .attr("fill", nodeColor)
          .attr("font-size", fontSize)
          .attr("font-weight", "normal");
      });

    }

    // svg canvas
    const svg = d3.create("svg")
      .attr("id", "depviz-graph")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [-width / 2, -height / 2, width, height]);

    // build the nodes
    const node = svg.append("g")
      .selectAll(null)
      .data(Object.values(nodes))
      .join("g")
      .attr("transform", d => `rotate(${d.angle}) translate(${radius},0)`)
      .append("text")
      .attr("id", d => `node-${d.objectId}`)
      .attr("x", d => d._x)
      .attr("y", d => d._y)
      .attr("dx", d => d.angle <= 90 ? "5" : "-5")
      .attr("dy", fontSize / 3)
      .attr("text-anchor", d => d.angle <= 90 ? "start" : "end")
      .attr("transform", d => d.angle > 90 ? "rotate(180)" : null)
      .attr("cursor", "pointer")
      .attr("fill", nodeColor)
      .attr("font-family", computedStyle.getPropertyValue("--font-family"))
      .attr("font-size", fontSize)
      .attr("font-weight", "normal")
      .text(d => d.name)
      .on("click", clicked)
      .on("mouseover", overed)
      .on("mouseout", outed);

    // build the links
    const link = svg.append("g")
      .selectAll(null)
      .data(Object.values(nodes).flatMap(d => d.outgoing))
      .join("g")
      .append("path")
      .attr("id", d => `link-${d.sourceId}-${d.targetId}`)
      .attr("class", d => `from-${d.sourceId} to-${d.targetId}`)
      .attr("fill", "none")
      .attr("opacity", "0.5")
      .attr("stroke", linkColor)
      .attr("stroke-linecap", "round")
      .attr("d", d => d.path);

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
                width: window.innerWidth - 4*parseInt(computedStyle.fontSize), // does not account for scrollbar width
                height: Math.max(window.innerHeight, 1200)
            }
        )
    );

}

// transform data into the expected format
const toJSON = (rawData, inputFormat, reverseTree) => {
    const data = {};

    // json input
    if (inputFormat === "json") {
        const jsonData = JSON.parse(rawData);

        // child -> parent[s]
        if (reverseTree) {

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

        // parent -> child[ren] (nothing to do)
        else {
            return jsonData;
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
                if (Object.keys(data).includes(p)) {
                    data[p].push(c);
                } else {
                    data[p] = [c];
                }
            }

        });
    }

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
