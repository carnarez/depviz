"""Convert a child -> list of parents JSON to `Mermaid` syntax.

Parameters
----------
: str
    Path to the JSON file(s).

Returns
-------
: str
    `Mermaid` diagram.

Usage
-----
```shell
$ python script.py <JSON FILE> [<JSON FILE> [...]]
```

Example
-------
```shell
$ python script.py dependencies.json
$ python script.py file1.json file2.json file3.json
```

"""

import json
import pathlib
import sys


def to_dot(objects: dict[str, list[str]]) -> str:
    r"""Convert the JSON content to `DOT` syntax.

    Parameters
    ----------
    objects : dict[str, list[str]]
        Dictionary of objects and upstream dependencie.

    Returns
    -------
    : str
        `DOT` diagram.

    """
    d = ""

    # build the list of unique nodes
    nodes: dict[str, int] = {}
    i = 0
    for n1, deps in objects.items():
        if n1 not in nodes:
            i += 1
            nodes[n1] = i
        for n2 in deps:
            if n2 not in nodes:
                i += 1
                nodes[n2] = i

    # nodes
    d += "  // nodes\n"
    for i, n in enumerate(nodes):
        d += f'  node{i} [label"{n}"]\n'

    # links
    d += "  // links\n"
    for n1 in objects:
        for n2 in objects:
            d += f"  node{nodes[n1]} -- node{nodes[n2]}\n"

    d += "}"

    return f"graph {{\n{d}\n}}"


def to_mmd(objects: dict[str, list[str]]) -> str:
    r"""Convert the JSON content to `Mermaid` syntax.

    Parameters
    ----------
    objects : dict[str, list[str]]
        Dictionary of objects and upstream dependencie.

    Returns
    -------
    : str
        `Mermaid` diagram.

    """
    # always top-bottom, manually change it if you want
    d = "graph TB\n"

    # build the list of unique nodes
    nodes: dict[str, int] = {}
    i = 0
    for n1, deps in objects.items():
        if n1 not in nodes:
            i += 1
            nodes[n1] = i
        for n2 in deps:
            if n2 not in nodes:
                i += 1
                nodes[n2] = i

    # nodes
    d += "  %% nodes\n"
    for i, n in enumerate(nodes):
        d += f"  node{i}({n})\n"

    # links
    d += "  %% links\n"
    for n1 in objects:
        for n2 in objects:
            d += f"  node{nodes[n1]} --- node{nodes[n2]}\n"

    return d


if __name__ == "__main__":
    func = None

    # command line arguments
    if "--dot" in sys.argv:
        sys.argv.remove("--dot")
        func = to_dot
    if "--mmd" in sys.argv and func is None:
        sys.argv.remove("--mmd")
        func = to_mmd

    # crash and burn
    if func is None:
        msg = "No known syntax provided"
        raise NotImplementedError(msg)

    # convert each provided file
    for a in sys.argv[1:]:
        with pathlib.Path(a).open() as f:
            sys.stdout.write(func(json.loads(f.read())))
