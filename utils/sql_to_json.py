"""Extract objects and their parents from SQL statements.

Parameters
----------
: str
    Path to the SQL script, containing more than one SQL statement.

Returns
-------
: str
    JSON-formatted, nested list of object and dependencies.

Usage
-----
```shell
$ python script.py <SQL FILE> [<SQL FILE> [...]]
```

Example
-------
```shell
$ python script.py views.sql
$ python script.py fact_*.sql dim_*.sql
```
"""

import json
import re
import sys

import sqlparse


def clean_query(query: str) -> str:
    r"""Deep-cleaning of a SQL query via
    [`sqlparse`](https://github.com/andialbrecht/sqlparse) and regular expressions.

    Parameters
    ----------
    query : str
        The SQL query.

    Returns
    -------
    : str
        Cleaned up query.

    Notes
    -----
    1. `sqlparse` tries to set all supported SQL statements to uppercase.
    2. Further cleaning is done via the following regular expressions:
        * `"/\*.*\*/"` -> `""`: remove remaining multiline comments;
        * `"--.*"` -> `""`: remove remaining inline comments;
        * `"([(,)])"` -> `" , "`: single spaces around function parameters;
        * `"([A-Za-z0-9_]+)\s*\.\s*([A-Za-z0-9_]+)"` -> `"[...].[...]"`: remove spaces
          around object descriptors;
        * `"(.*)\s*=\s*(.*)"` -> `"[...] = [...]"`: single spaces around equal signs;
        * `"(.*)\s*\|\|\s*(.*)` -> `"[...] || [...]"`: single spaces around
          concatenation operators;
        * `"(.*)\s*::\s*(.*)"` -> `"[...]::[...]"`: remove spaces around datatyping
          operators;
        * `"[\s]+"` -> `" "`: replace multiple spaces by single spaces.
    """
    # good effort, but does not know some functions/keywords
    q = sqlparse.format(query, keyword_case="lower", strip_comments=True)

    # regular cleaning
    q = re.sub(r"/\*.*\*/", "", q, flags=re.DOTALL)
    q = re.sub(r"--.*", "", q)
    q = re.sub("([(,)])", r" \1 ", q)
    q = re.sub(r"([A-Za-z0-9_]+)\s*\.\s*([A-Za-z0-9_]+)", r"\1.\2", q)
    q = re.sub(r"(.*)\s*=\s*(.*)", r"\1 = \2", q)
    q = re.sub(r"(.*)\s*\|\|\s*(.*)", r"\1 || \2", q)
    q = re.sub(r"(.*)\s*::\s*(.*)", r"\1::\2", q)
    q = re.sub(r"[\s]+", " ", q).strip()

    return q


def fetch_objects(query: str, objects: dict[str, list[str]]) -> tuple[str, list[str]]:
    r"""Extract materialized view object and its dependencies from a SQL statement.

    Parameters
    ----------
    query : str
        The DDL to parse.
    objects : dict[str, list[str]]
        List of objects and parents already parsed.

    Returns
    -------
    : dict[str, list[str]]
        Updated list of objects and children.

    Notes
    -----
    1. Only materialized views are checked.
    2. Supported SQL statements and associated regular expressions:
        * `CREATE\s+[A-Za-z]*\s+MATERIALIZED\s+VIEW\s+([^(].*?)\s``
        * `FROM\s+(\S+rated\.[^(\s;)]+)`
        * `JOIN\s+(\S+rated\.[^(\s;)]+)`
    """
    cr = r"create\s+materialized\s+view\s+([^(].*?)\s"
    pr = (r"from\s+(\S+rated\.[^(\s;)]+)", r"join\s+(\S+rated\.[^(\s;)]+)")

    # current object
    if (m := re.search(cr, query)) is not None:
        c = m.group(1)

        # parent object(s)
        p = []
        for r in pr:
            for m in re.finditer(r, query):
                if (o := m.group(1)) not in p:
                    p.append(o)

        # store the object
        for o in p:
            if o not in objects:
                objects[o] = [c]
            else:
                objects.append(c)

    return objects


if __name__ == "__main__":
    o: dict[str, list[str]] = {}

    # parse each statement in each script provided
    for a in sys.argv[1:]:
        with open(a) as f:
            for s in sqlparse.split(f.read()):
                q = clean_query(s)
                o = fetch_objects(q, o)

    # output
    print(json.dumps(o))
