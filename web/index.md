Below links to various visualisations[^1] for dependency networks:

* [Hierarchical Edge Bundling](/hierarchical-edge-bundling): allows visualising
  _adjacency relations_ between entities organized in a _hierarchy_. The idea is to
  bundle the adjacency edges together to decrease the clutter usually observed in
  complex networks.[^2]

This austere little thing is mostly for my own use as I find myself exporting (from
libraries or databases) dependency trees and the likes. Instead of writing something
ad-hoc each time, this page allows me to quickly visualise and demonstrate.

As an example, below the query to export all dependencies between materialized views
within an AWS `Redshift` database:[^3]

```sql
select
  parent || ',' || child
from (
  select
    ref_schema || '.' || ref_name as parent,
    "schema" || '.' || "name" as child
  from stv_mv_deps
  order by 1,2
)
```

This would output some CSV-looking list that I can directly copy/paste in the
visualisation input form of these pages.

Also available in this repo, some `Python` [utils](/utils) to extract information from
SQL queries or convert tabular CSV content to the JSON input some of the visualisations
expect. Run via:

```shell
$ make env
> python utils/csv_to_json.py <CSV FILE>  # for instance
```

[^1]: Mostly done using [D3](https://d3js.org/) because this library rocks, and the SVG
      format is fun to work with.
[^2]: A quote from a [source](https://www.data-to-viz.com/graph/edge_bundling.html).
[^3]: Here is a [link](https://aws.amazon.com/redshift/) to avoid lawsuits; not an
      advertisement though, simply what I am currently working with.
