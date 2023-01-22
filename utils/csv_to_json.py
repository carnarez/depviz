"""Extract objects and their parents from SQL statements.

Parameters
----------
: str
    Path to the CSV file.

Returns
-------
: str
    JSON-formatted, nested list of object and dependencies.

Usage
-----
```shell
$ python script.py <CSV FILE> [<CSV FILE> [...]]
```

Example
-------
```shell
$ python script.py dependencies.sql
$ python script.py deps-dev.csv deps-prd.csv
```
"""

import json
import sys


def convert_csv(content: str, objects: dict[str, list[str]]) -> tuple[str, list[str]]:
    r"""Convert the CSV content to JSON.

    Parameters
    ----------
    content : str
        The CSV content to parse and convert.
    objects : dict[str, list[str]]
        List of objects and parents already parsed.

    Returns
    -------
    : dict[str, list[str]]
        Updated list of objects and children.

    Notes
    -----
    Expects a two columns dataset, each line embedding a `child,parent` pair.
    """
    for r in content.split("\n"):
        if len(r.strip()):
            c, p = r.split(",")

            # list dependencies as parent -> child(ren)
            if p in objects:
                objects[p].append(c)
            else:
                objects[p] = [c]

    return objects


if __name__ == "__main__":
    o: dict[str, list[str]] = {}

    # parse each file
    for a in sys.argv[1:]:
        with open(a) as f:
            o = convert_csv(f.read(), o)

    # output
    print(json.dumps(o))
