"""Build an object -> upstream dependencies JSON object from CSV content.

Parameters
----------
: str
    Path to the CSV file(s).

Returns
-------
: str
    JSON-formatted, nested list of object and upstream dependencies (objects that are
    depended on).

Usage
-----
```shell
$ python script.py <CSV FILE> [<CSV FILE> [...]]
```

Example
-------
```shell
$ python script.py dependencies.csv
$ python script.py file1.csv file2.csv file3.csv
```
"""

import json
import sys


def to_json(content: str, objects: dict[str, list[str]]) -> tuple[str, list[str]]:
    r"""Convert the CSV content to JSON.

    Parameters
    ----------
    content : str
        The CSV content to parse and convert.
    objects : dict[str, list[str]]
        Dictionary of objects already parsed.

    Returns
    -------
    : dict[str, list[str]]
        Updated dictionary of objects and upstream dependencies.

    Notes
    -----
    Expects a two columns dataset, each line embedding a `object1,object2` pair; the
    second object is expected to be depended upon.
    """
    for r in content.split("\n"):
        if len(r.strip()):
            c, p = r.split(",")

            # list dependencies as parent -> (list of) child(ren)
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
            o = to_json(f.read(), o)

    # output
    print(json.dumps(o))
