"""Extract upstream dependencies from SQL files, each containing a single query.

Parameters
----------
: str
    Path to the SQL script(s), each containing a _singled out_ SQL query.

Returns
-------
: str
    JSON-formatted, nested list of objects and associated list of upstream dependencies.
    One can see this object as child -> list of parents.

Usage
-----
```shell
$ python script.py <SQL FILE> [<SQL FILE> [...]]
$ python script.py <SQL FILE> [<SQL FILE> [...]] --pretty
```

Example
-------
```shell
$ python script.py view.sql --pretty
$ python script.py fact_*.sql dim_*.sql
```

Note
----
* Only a few SQL statements amongst the gazillions ways to write them are supported;
  feel free to drop a message with a new one to test.
* This is based on queries running on `Redshift`, no guarantees this would work on any
  other syntax (but `Redshift` is largely based on `PostgreSQL`, there's hope).
* This little stunt is still in alpha, and a lot more testing is required!
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
    q = re.sub(r"[\s]+", " ", q)
    q = q.strip()

    return q


def split_query(query: str) -> dict[str, list[str]]:
    r"""Split a query in its subqueries, if any.

    Parameters
    ----------
    query : str
        The DDL to parse.

    Returns
    -------
    : dict[str, list[str]]
        Dictionary of [sub]queries and associated DDL, split in parts if the `union`
        keyword is found.

    Notes
    -----
    Processing goes as follows:

    1. Search for `... as ( select ... )` CTE statement via the
       `[^\s]+\s+AS\s+\(\s+SELECT` regular expression.
    2. Read each character from there, keeping count of opening/closing brackets; once
       this number reaches zero (or we seeked to end of the query) we are done with the
       subquery.
    3. Store the subquery (split on the `UNION` keyword, if any) under the CTE name.
    4. Move on to the next subquery.
    5. Extract the main query, if any, using the following regular expressions (these
       could be factored a bit further but clarity prevails):
        * `CREATE\s+EXTERNAL\s+TABLE\s+([^\s]+)`
        * `CREATE\s+TABLE\s([^\s]+)`
        * `CREATE\s+MATERIALIZED\s+VIEW\s([^\s]+)`
        * `CREATE\+OR\s+REPLACE\s+VIEW\s([^\s]+)`
        * `CREATE\s+VIEW\s([^\s]+)`
    """
    parts: dict[str, list[str]] = {}

    # extract subqueries
    n = len(query) + 1
    while n != len(query):
        n = len(query)

        # find a match
        if (m := re.search(r"([^\s]+)(\s+as\s+)(\(\s+select)", query)) is not None:
            n = m.group(1)  # name of the cte
            i = m.end(2)  # start of the subquery
            b = 0  # number of open brackets
            s = ""  # stored characters

            read = True  # store the characters until false
            while read:

                # count opening/closing brackets; if counts reaches 0 we are done
                if query[i] == "(":
                    b += 1
                if query[i] == ")":
                    b -= 1
                    if b == 0:
                        read = False

                # end of the query
                try:
                    s += query[i]
                except IndexError:
                    read = False

                # iterate
                i += 1

            # save the part(s)
            if re.search(r"from\s+\(\s+select", s) is not None:
                parts[n] = [s.strip().lstrip("(").rstrip(")").strip()]
            else:
                parts[n] = list(
                    map(
                        str.strip,
                        re.split(r"union[ all]*", s.strip().lstrip("(").rstrip(")")),
                    )
                )

            # remove the part(s) from the query and iterate
            query = query.replace(f"{n}{m.group(2)}{s}", f"%SUBQUERY:{n}%", 1)

    # remove column selection
    for m in re.finditer(r"select\s+(.*?)\s+from\s+[^\s(]+", query):
        query = query.replace(m.group(1), "%COLUMNS%")

    # extract main query, if any (if the query does not generate any object, this step
    # returns nothing)
    for r in (
        r"create\s+external\s+table\s+([^\s]+)",
        r"create\s+table\s([^\s]+)",
        r"create\s+materialized\s+view\s([^\s]+)",
        r"create\+or\s+replace\s+view\s([^\s]+)",
        r"create\s+view\s([^\s]+)",
    ):
        if (m := re.search(r, query, flags=re.IGNORECASE)) is not None:
            parts[m.group(1)] = list(map(str.strip, re.split(r"union[ all]*", query)))
            break

    # debug
    # print(query)

    return parts


def fetch_dependencies(parts: dict[str, list[str]]) -> dict[str, list[str]]:
    r"""Fetch upstream dependencies from each subquery.

    Parameters
    ----------
    : dict[str, list[str]]
        Dictionary of [sub]queries and associated DDL.

    Returns
    -------
    : dict[str, list[str]]
        Dictionary of objects and associated list of upstream dependencies.

    Notes
    -----
    Supported regular expressions (_e.g._, SQL statements):

    1. `FROM\s+([^\s(]+)`
    2. `JOIN\s+([^\s(]+)`
    3. `LOCATION\s+'(s3://.+)'` (`Redshift` stuff)
    """
    tree: dict[str, list[str]] = {}

    # iterate over each object -> associated subqueries
    for n, p in parts.items():
        for q in p:
            if any([f" {s} " in q.lower() for s in ("from", "join", "location")]):
                for r in (r"from\s+([^\s(]+)", r"join\s+([^\s(]+)", r"location\s+'(s3://.+)'"):
                    for m in re.finditer(r, q, flags=re.IGNORECASE):
                        if n in tree:
                            if m.group(1) not in tree[n]:
                                tree[n].append(m.group(1))
                        else:
                            tree[n] = [m.group(1)]
            else:
                tree[n] = []

    return tree


if __name__ == "__main__":
    o: dict[str, list[str]] = {}

    # command line argument
    if "--pretty" in sys.argv:
        sys.argv.remove("--pretty")
        indent = 4
    else:
        indent = None

    # parse each statement in each script provided
    for a in sys.argv[1:]:
        with open(a) as f:
            for q in sqlparse.split(f.read()):
                q = clean_query(q)
                p = split_query(q)
                t = fetch_dependencies(p)

            # output
            print(json.dumps(t, indent=indent))
