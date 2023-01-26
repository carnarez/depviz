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

##### [Directed acyclic graph](/directed-acyclic-graph)

Also called _Sugiyama_ after the author of the original publication solving the layout
optimization problem back in the days. [^3]

The implementation uses the [`d3-dag`](https://github.com/erikbrinkman/d3-dag) package.
Check some more fun examples on
[Observable](https://observablehq.com/search?query=d3-dag).

##### [Force-directed graph](/force-directed-graph)

In 3D.

The most fun, if not the most practical to demonstrate. But hey, it makes people smile.

Based on the [`3d-force-graph`](https://github.com/vasturiano/3d-force-graph) package,
and the excellent series of examples around it. Itself making use of the now well-known
[`three.js`](https://github.com/mrdoob/three.js) and its WebGL rendering.

##### [Hierarchical edge bundling](/hierarchical-edge-bundling)

My personal favourite to visualise multilevel dependency networks. According to the
author of [_From Data to Viz_](https://www.data-to-viz.com/): [^4]

> Hierarchical edge bundling allows visualising adjacency relations between entities
> organized in a hierarchy. The idea is to bundle the adjacency edges together to
> decrease the clutter usually observed in complex networks.

Well said.

#### [Tooling](/utils)

Also available in this repo, some small `Python` utils to extract information from SQL
queries or convert tabular CSV content to the JSON input some of the visualisations
expect. Run via:

```shell
$ make env
> python utils/csv_to_json.py <CSV FILE>  # for instance
```

[^1]: Here is a [link](https://aws.amazon.com/redshift/) to avoid lawsuits; not an
      advertisement though, simply what I am currently working with.
[^2]: Mostly done using [D3](https://d3js.org/) because this library rocks, and the SVG
      format is fun to work with.
[^3]: _Methods for Visual Understanding of Hierarchical System Structures_ by Sugiyama
      _et al._, 1981
[^4]: The quote from the [source](https://www.data-to-viz.com/graph/edge_bundling.html).
