// load necessary scripts (add them to the <head> section)
// chaining them as everything loading after the page is ready will be done
// asynchronously, but some need others (three-spritetext.js needs three.js for
// instance)
// could have done something with promises but it is currently past midnight and i have
// to work early tomorrow
const s = document.createElement("script");
s.src = "https://unpkg.com/three";
s.onload = () => {
    console.log("Loaded three.js");
    const s = document.createElement("script");
    s.src = "https://unpkg.com/three-spritetext";
    s.onload = () => {
        console.log("Loaded three-spritetext.js");
        const s = document.createElement("script");
        s.src = "https://unpkg.com/3d-force-graph";
        s.onload = () => {
            console.log("Loaded 3d-force-graph.js");
        }
        document.head.appendChild(s);
    }
    document.head.appendChild(s);
}
document.head.appendChild(s);

// fetch browser-calculated styling properties
const computedStyle = window.getComputedStyle(document.documentElement);

// https://github.com/vasturiano/3d-force-graph/blob/master/example/highlight/index.html
// https://github.com/vasturiano/3d-force-graph/blob/master/example/text-nodes/index.html
// below are the default options for to render the graph
const generateGraph = (
    data,
    {
        backgroundColor = "#eee", // background color
        nodeColor = "#000", // node color
        linkColor = "#000", // link color
        colorIncoming = "#07f", // link color for parents
        colorOutgoing = "#f77", // link color for children
        withLabels = false, // whether nodes should carry the objet names
        width = 800, // outer width, in pixels
        height = 800 // outer height, in pixels
    } = {}
) => {

    const incomingNodes = {},
          outgoingNodes = {},
          incomingLinks = {},
          outgoingLinks = {};

    // object.id -> object
    const _nodes = data.nodes.reduce((o, n) => ({...o, [n.id]: n}), {}),
          _links = data.links.reduce((o, l) => ({...o, [l.id]: l}), {});

    // build the list of neighbouring nodes
    data.links.forEach(l => {

        // incoming
        if (Object.keys(incomingLinks).includes(l.target)) {
            incomingLinks[l.target].push(l);
        } else {
            incomingLinks[l.target] = [l];
        }

        if (Object.keys(incomingNodes).includes(l.target)) {
            incomingNodes[l.target].push(_nodes[l.source]);
        } else {
            incomingNodes[l.target] = [_nodes[l.source]];
        }

        // outgoing
        if (Object.keys(outgoingLinks).includes(l.source)) {
            outgoingLinks[l.source].push(l);
        } else {
            outgoingLinks[l.source] = [l];
        }

        if (Object.keys(outgoingNodes).includes(l.source)) {
            outgoingNodes[l.source].push(_nodes[l.target]);
        } else {
            outgoingNodes[l.source] = [_nodes[l.target]];
        }

    });

    // general properties
    const g = ForceGraph3D()(document.getElementById("depviz-graph"))
      .width(width)
      .height(height)
      .backgroundColor(backgroundColor)
      .showNavInfo(false)
      .graphData(data);

    // keep track of the highlighted objects
    const highlightedIncomingNodes = new Set(),
          highlightedOutgoingNodes = new Set(),
          highlightedIncomingLinks = new Set(),
          highlightedOutgoingLinks = new Set();

    // define the colour of [highlighted] objects
    const setHighlightedColor = (object, highlightedIncoming, highlightedOutgoing) => {
        if (highlightedIncoming.has(object)) {
            return colorIncoming;
        } else if (highlightedOutgoing.has(object)) {
            return colorOutgoing;
        } else {
            return linkColor;
        }
    }

    // nodes
    if (withLabels) {

        // create label for the nodes
        g.nodeThreeObject(n => {
            const sprite = new SpriteText(n.id);
            sprite.color = nodeColor;
            sprite.material.depthWrite = false; // make sprite background transparent
            sprite.textHeight = parseInt(computedStyle.fontSize) / 2;
            return sprite;
        });

        // spread nodes a little wider
        g.d3Force("charge").strength(-500);

    } else {

        // balls
        g.nodeColor(n => {
              return setHighlightedColor(
                  n, highlightedIncomingNodes, highlightedOutgoingNodes
              );
          })
          .nodeLabel(n => `<span class="depviz-labels">${n.id}</span>`)
          .nodeOpacity(1)
          .nodeResolution(16);

    }

    // links
    g.linkColor(l => {
          return setHighlightedColor(
              l, highlightedIncomingLinks, highlightedOutgoingLinks
          );
      })
      .linkOpacity(1)
      .linkWidth(l => {
          if (highlightedIncomingLinks.has(l) || highlightedOutgoingLinks.has(l)) {
              return 1;
          } else {
              return 0.3;
          }
      })
      .linkResolution(12)
      .linkDirectionalParticles(3)
      .linkDirectionalParticleWidth(l => {
          if (highlightedIncomingLinks.has(l) || highlightedOutgoingLinks.has(l)) {
              return 1.5;
          } else {
              return 0;
          }
      })
      .linkDirectionalParticleResolution(12);

    // highlight nodes and links
    g.onNodeHover(n => {

        // cleanup
        highlightedIncomingNodes.clear();
        highlightedOutgoingNodes.clear();
        highlightedIncomingLinks.clear();
        highlightedOutgoingLinks.clear();

        // hovering in (hovering out throws an exception)
        if (n) {
            if (Object.keys(incomingLinks).includes(n.id))
                incomingLinks[n.id].forEach(l => {
                    highlightedIncomingLinks.add(l);
                    highlightedIncomingNodes.add(l.source);
                });
            if (Object.keys(outgoingLinks).includes(n.id))
                outgoingLinks[n.id].forEach(l => {
                    highlightedOutgoingLinks.add(l)
                    highlightedOutgoingNodes.add(l.target);
                });
        }

        // update objet properties
        g.nodeColor(g.nodeColor());
        g.linkColor(g.linkColor());

    });

}

// process the posted data and draw the svg
const drawGraph = (data, opts = {}) => {

    // add the element to the page
    const d = document.createElement("div");
    d.id = "depviz-graph"
    document.getElementById("depviz").appendChild(d);

    // generate and add the graph to the element
    generateGraph(
        data,
        {
            backgroundColor: computedStyle.getPropertyValue("--background-color"),
            nodeColor: computedStyle.getPropertyValue("--font-color"),
            linkColor: computedStyle.getPropertyValue("--font-color"),
            colorIncoming: computedStyle.getPropertyValue("--link-color"),
            width: window.innerWidth,
            height: window.innerHeight - document.querySelector("nav").getBoundingClientRect().height - 1,
            ...opts
        }
    )

}

// transform data into the expected format
const toJSON = (rawData, inputFormat, reverseTree) => {
    const data = {"nodes": [], "links": []},
          nodes = [],
          links = [];

    let c = "", // child
        p = ""; // parent

    // json input
    if (inputFormat === "json") {
        const jsonData = JSON.parse(rawData);

        // build the json data
        Object.keys(jsonData).forEach(o1 => {

            // add the object to the list of nodes
            if (!nodes.includes(o1)) {
                nodes.push(o1);
                data.nodes.push({"id": o1});
            }

            jsonData[o1].forEach(o2 => {

                // add the object to the list of nodes
                if (!nodes.includes(o2)) {
                    nodes.push(o2);
                    data.nodes.push({"id": o2});
                }

                // child -> parent[s]
                if (reverseTree) {
                    c = o1;
                    p = o2;
                }
                // parent -> child[ren]
                else {
                    p = o1;
                    c = o2;
                }

                // add relationship between objects to the list of links
                const l = `${p}-${c}`;
                if (!links.includes(l)) {
                    links.push(l);
                    data.links.push({"id": l, "source": p, "target": c});
                }

            });
        });

    }

    // csv input
    else {
        rawData.split("\n").forEach(l => {

            // child -> parent[s]
            if (reverseTree) {
                [c, p] = l.split(",").map(o => o.trim());
            }

            // parent -> child[ren]
            else {
                [p, c] = l.split(",").map(o => o.trim());
            }

            if (c && p && c.length && p.length) {

                // add the object to the list of nodes
                if (!nodes.includes(c)) {
                    nodes.push(c);
                    data.nodes.push({"id": c});
                }
                if (!nodes.includes(p)) {
                    nodes.push(p);
                    data.nodes.push({"id": p});
                }

                // add relationship between objects to the list of links
                const l = `${p}-${c}`;
                if (!links.includes(l)) {
                    links.push(l);
                    data.links.push({"id": l, "source": c, "target": p});
                }

            }

        });
    }

    return data;
}

// add the form to the page
document.getElementById("depviz").innerHTML += `
<div id="depviz-form">
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
  <input id="depviz-labels" type="checkbox">
  <label for="depviz-labels">Labels</label>
</div>
<div class="depviz-buttons">
  <a id="depviz-button">Submit</a>
</div>
`;

// event listener
document.getElementById("depviz-button").addEventListener("click", (event) => {

    // convert to input expected by the rendering function
    const data = toJSON(
        document.getElementById("depviz-raw").value,
        (document.getElementById("depviz-json").checked) ? "json" : "csv",
        (document.getElementById("depviz-reverse").checked) ? true : false
    );

    // gather option values
    const opts = {
        "withLabels": document.getElementById("depviz-labels").checked
    };

    // remove the form and all other bottom stuff
    document.querySelectorAll("article > *:not(.maintext)").forEach(e => {
        e.style.display = "none";
    });
    document.querySelectorAll(".maintext > *:not(#depviz)").forEach(e => {
        e.style.display = "none";
    });
    document.querySelectorAll("#depviz > *:not(#depviz-graph)").forEach(e => {
        e.style.display = "none";
    });
    document.getElementById("depviz").style.margin = 0;

    // draw the graph
    drawGraph(data, opts);

});
