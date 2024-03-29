This austere little set of pages is mostly for my own use as I find myself exporting
(from libraries or databases) dependency trees and the likes. Instead of writing
something ad-hoc each time, this page allows me to quickly visualise and demonstrate.

As an example, below the query to export all dependencies between materialized views
within an AWS `Redshift` database: [^1]

```sql
select
  parent || ',' || child as "csv"
from (
  select
    ref_schema || '.' || ref_name as parent,
    "schema" || '.' || "name" as child
  from pg_catalog.stv_mv_deps
  order by 1,2
)
```

This would output some CSV-looking list that I can directly copy/paste in the
visualisation input form of these pages. Below some links to various visualisations [^2]
to plot such networks.

#### Visualisation options

##### [Force-directed graph](/force-directed-graph)

In 3D.

The most fun, if not the most practical to demonstrate. But hey, it makes people smile.

Based on the [`3d-force-graph`](https://github.com/vasturiano/3d-force-graph) package,
and the excellent series of examples around it. Itself making use of the now well-known
[`three.js`](https://github.com/mrdoob/three.js) and its WebGL rendering.

##### [`Graphviz`](/graphviz-graph)

The drawing engine written in `C`, [`Graphviz`](https://graphviz.org/), has now been
[compiled to WASM](https://hpcc-systems.github.io/hpcc-js-wasm/classes/graphviz.Graphviz.html)
by the folks at [HPCC Systems](https://hpccsystems.com/), making it usable in browsers.

Beware, expect old-school graphics.

##### [Hierarchical edge bundling](/hierarchical-edge-bundling)

My personal favourite to visualise multilevel dependency networks. According to the
author of [_From Data to Viz_](https://www.data-to-viz.com/): [^3]

> Hierarchical edge bundling allows visualising adjacency relations between entities
> organized in a hierarchy. The idea is to bundle the adjacency edges together to
> decrease the clutter usually observed in complex networks.

Well said.

##### [`Mermaid`](/mermaid-flowchart)

Following the _Sugiyama_ method after the author of the original publication solving the
layout optimization problem back in the days. [^4]

Graph built via [`Mermaid`](https://github.com/mermaid-js/mermaid)
([docs](https://mermaid.js.org/)), a somewhat broader implementation of the DAG solution
presented above defining its own [syntax](https://mermaid.js.org/syntax/flowchart.html)
(generated in these pages from the provided data) and based on yet another rendering
engine: [`dagre-d3`](https://github.com/dagrejs/dagre-d3) (now officially deprecated but
still working well).

#### Input formats

Most of these litle tools accept data in the following formats: CSV in which each line
carries a pair of `parent,child` or `child,parent`:

```csv
parent,child
parent,child
...
```

or JSON in which a list of children is provided for each parent, or a list of parents
for each child:

```json
{
  parent: [
    child,
    child,
    ...
  ],
  parent : [
    ...
  ],
  ...
}
```

Look for the buttons to precise which input format is provided to avoid swaping up the
colour coding. And let's keep it consistent, no mixing between the formats in the same
file.

Most of these representation colour parent link(s) / node(s) in blue, and child link(s)
/ node(s) in red.

#### [Tooling](/utils)

Also available in this repo, some small `Python` utils to extract information from SQL
queries or convert tabular CSV content to the JSON input some of the visualisations
expect. Run via:

```shell
$ make env
> python utils/csv_to_json.py <CSV FILE>  # for instance
```

Again, this works for _me_ and my current projects! No other claims nor guarantees. 

[^1]: Here is a [link](https://aws.amazon.com/redshift/) to avoid lawsuits; not an
      advertisement though, simply what I am currently working with.
[^2]: Mostly done using [D3](https://d3js.org/) because this library rocks, and the SVG
      format is fun to work with.
[^3]: The quote from the [source](https://www.data-to-viz.com/graph/edge_bundling.html).
[^4]: _Methods for Visual Understanding of Hierarchical System Structures_ by Sugiyama
      _et al._, 1981
