"""Fetch all objects related to another one, regardless of the depth.

Parameters
----------
: str
    Name of the object to filter for.
: str
    Path to the JSON file(s).

Returns
-------
: str
    JSON-formatted, nested list of object and upstream dependencies (objects that are
    depended on).

Usage
-----
```shell
$ python script.py <OBJECT NAME> <JSON FILE> [<JSON FILE> [...]]
```

Example
-------
```shell
$ python script.py fact_thing dependencies.json
$ python script.py dim_whatever file1.json file2.json file3.json
```

"""

import json
import pathlib
import sys


def filter_json(
    name: str,
    objects: dict[str, list[str]],
    _objects: dict[str, list[str]] | None = None,
) -> dict[str, list[str]]:
    r"""Fetch all objects related to a single object, regardless of the depth.

    Parameters
    ----------
    name : str
        Name of the object to filter for.
    objects : dict[str, list[str]]
        Dictionary of objects and upstream dependencies.
    _objects : dict[str, list[str]]
        Dictionary of objects already parsed.

    Returns
    -------
    : dict[str, list[str]]
        Filtered list of upstream and downstream dependencies.

    """
    _objects = {} if _objects is None else _objects

    included: list[str] = []

    # filter until the size of the list does not change anymore
    maxn = 1e99
    while len(included) != maxn:
        maxn = len(included)

        # run through all the nodes
        # expensive if a lot of objects are involved
        for n, deps in objects.items():
            if n == name or n in included:
                for d in deps:
                    if d not in included:
                        included.append(d)

    # all objects along the lineage
    for i in included:
        if i in objects and i not in _objects:
            _objects[i] = objects[i]

    return _objects


if __name__ == "__main__":
    n: str = sys.argv[1]
    o: dict[str, list[str]] = {}

    # convert ecah provided file
    for a in sys.argv[2:]:
        with pathlib.Path(a).open() as f:
            o = filter_json(a, o)

    # filter
    sys.stdout.write(json.dumps(o))
