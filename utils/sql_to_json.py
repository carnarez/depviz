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
import pathlib
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
        * `"(.*)\s*[<=>]+\s*(.*)"` -> `"[...] = [...]"`: single spaces around equal,
          greater or less than signs (or combinations thereof);
        * `"(.*)\s*\|\|\s*(.*)` -> `"[...] || [...]"`: single spaces around
          concatenation operators;
        * `"(.*)\s*::\s*(.*)"` -> `"[...]::[...]"`: remove spaces around datatyping
          operators;
        * `"[\s]+"` -> `" "`: replace multiple spaces by single spaces;
        * `";$"` -> `""`: remove final semicolumn (`;`).

    """
    # good effort, but does not know some functions/keywords
    q = sqlparse.format(query, keyword_case="lower", strip_comments=True)

    # regular cleaning
    q = re.sub(r"/\*.*\*/", "", q, flags=re.DOTALL)
    q = re.sub("--.*", "", q)
    q = re.sub("([(,)])", r" \1 ", q)
    q = re.sub(r"([A-Za-z0-9_]+)\s*\.\s*([A-Za-z0-9_]+)", r"\1.\2", q)
    q = re.sub(r"(.*)\s*[<=>]+\s*(.*)", r"\1 = \2", q)
    q = re.sub(r"(.*)\s*\|\|\s*(.*)", r"\1 || \2", q)
    q = re.sub(r"(.*)\s*::\s*(.*)", r"\1::\2", q)
    q = re.sub(r"[\s]+", " ", q)
    q = re.sub(";$", "", q)
    q = q.strip()

    return q


def clean_functions(query: str) -> str:
    r"""Escape `FROM` operators in SQL functions.

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
    Currently testing for the following regular expression:

    * `"(\(\s+['\"].+?['\"]\s+)FROM(\s+\S+?\s+\))"`: match function parameters including
      quoted keywords and the `FROM` keyword,
    * `"(\(\s+\S+?\s+)FROM(\s+\S+?\s+\))"`: match function parameters including regular
      unquoted keywords and the `FROM` keyword,
    * `"(\(\s+\S+?\s+)FROM(\s+\S+?\s+\()"`: ``.

    The `FROM` from the matched pattern will be replaced by `%FROM%` not to be matched
    by the follow up processing.

    """
    # clean up the query until its length does not change anymore
    maxn = 1e99
    while len(query) != maxn:
        maxn = len(query)

        # test for various cases; kind of expect a query that went through the
        # clean_query() function first as it does not account for multiline text
        for r in (
            r"(\(\s+['\"].+?['\"]\s+)from(\s+\S+?\s+\))",
            r"(\(\s+\S+?\s+)from(\s+\S+?\s+\))",
            r"(\(\s+\S+?\s+)from(\s+\S+?\s+\()",  # reversed bracket
        ):
            for m in re.finditer(r, query):
                query = query.replace(m.group(0), f"{m.group(1)}%FROM%{m.group(2)}")

    return query


def _split(
    query: str, parts: dict[str, str] | None = None
) -> tuple[str, dict[str, str]]:
    r"""Extract and parse subqueries from a query (or subquery).

    Parameters
    ----------
    query : str
        The DDL to parse.
    parts : dict[str, list[str]]
        Dictionary of [sub]queries and associated DDL that were already parsed.

    Returns
    -------
    : str
        The query, cleaned from its parts.
    : dict[str, list[str]]
        Dictionary of [sub]queries and associated DDL, split in parts if the `UNION`
        keyword is found.

    Note
    ----
    A subquery is identified as a CTE, _i.e._, `... as ( select ... )`. The following
    regular expression is used: `[^\s]+\s+AS\s+\(\s+SELECT`.

    """
    parts = {} if parts is None else parts

    # regular expression to catch subquery
    r = r"([^\s]+)(\s+as\s+)(\(\s+select)"

    # extract subqueries until the length of the string does not change anymore
    maxn = 1e99
    while len(query) != maxn:
        maxn = len(query)

        # find a match
        if (m := re.search(r, query)) is not None:
            n = m.group(1)  # name of the subquery
            a = m.group(2)  # ... as ...
            i = m.end(2)  # start of the subquery
            b = 0  # number of open/close brackets
            s = ""  # stored characters

            read = True  # store the characters until false
            while read:
                # fetch the next character
                try:
                    c = query[i]
                except IndexError:
                    c = None

                # count opening/closing brackets
                b += 1 if c == "(" else 0
                b -= 1 if c == ")" else 0

                # add the character to the stored string
                s += c if c is not None else ""

                # iterate
                i += 1

                # stop reading when the counts reach 0
                if not b or c is None:
                    read = not read

            # remove the part(s) from the query and iterate
            query = query.replace(f"{n}{a}{s}", f"%SUBQUERY:{n}%", 1)

            # call itself over the subquery if it needs to be parsed further (subquery
            # within subquery)
            if re.search(r, s) is not None:
                s, parts = _split(s.strip(), parts)

            # clean up further to make it readable
            s = re.sub(r"select\s+(.*?)\s+from", "select %COLUMNS% from", s)

            # store the query and its parts
            parts[n] = s

    return query, parts


def split_query(query: str) -> dict[str, str]:
    r"""Split a query in its subqueries, if any.

    Parameters
    ----------
    query : str
        The DDL to parse.

    Returns
    -------
    : dict[str, str]
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
    3. Store the subquery under the CTE name.
    4. Recursively search for new CTE statements within the subquery, if any.
    5. Move on to the next subquery.
    6. Extract the main query, if any, using the following regular expressions (these
       could be factored a bit further but clarity prevails):
        * `CREATE\s+EXTERNAL\s+TABLE\s+([^\s]+)`
        * `CREATE\s+TABLE\s([^\s]+)`
        * `CREATE\s+MATERIALIZED\s+VIEW\s([^\s]+)`
        * `CREATE\+OR\s+REPLACE\s+VIEW\s([^\s]+)`
        * `CREATE\s+VIEW\s([^\s]+)`

    """
    # recursively extract subqueries
    # make sure we start from empty parts
    query, parts = _split(query, {})
    maxn = len(parts)

    # extract main query, if any (if the query does not generate any object, this step
    # returns nothing)
    for r in (
        r"create\s+external\s+table\s+([^\s]+)",
        r"create\s+table\s([^\s]+)",
        r"create\s+materialized\s+view\s+([^\s]+)",
        r"create\s+or\s+replace\s+view\s+([^\s]+)",
        r"create\s+view\s+([^\s]+)",
    ):
        if (m := re.search(r, query, flags=re.IGNORECASE)) is not None:
            parts[m.group(1)] = re.sub(
                r"select\s+(.*?)\s+from", "select %COLUMNS% from", query
            )
            break

    # if not object was found, we still want to analyze the last statement
    if len(parts) == maxn:
        parts["SELECT"] = re.sub(
            r"select\s+(.*?)\s+from", "select %COLUMNS% from", query
        )

    # clean out unwanted objects (containing our "%SUBQUERY:" keyword for instance,
    # product of using extra brackets and the imperfect regular expressions above)
    for k in list(parts.keys()):
        if "%SUBQUERY:" in k:
            parts.pop(k)

    return parts


def fetch_dependencies(parts: dict[str, str]) -> dict[str, list[str]]:
    r"""Fetch upstream dependencies from each subquery.

    Parameters
    ----------
    parts : dict[str, list[str]]
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
        if any(f" {k} " in p.lower() for k in ("from", "join", "location")):
            for r in (
                r"\s+from\s+([^\s(]+)",
                r"\s+join\s+([^\s(]+)",
                r"\s+location\s+'(s3://.+)'",
            ):
                for m in re.finditer(r, p, flags=re.IGNORECASE):
                    if n in tree:
                        if m.group(1) not in tree[n]:
                            tree[n].append(m.group(1))
                    else:
                        tree[n] = [m.group(1)]
        else:
            tree[n] = []

        # order the dependencies
        tree[n].sort()

    return tree


if __name__ == "__main__":
    o: dict[str, list[str]] = {}

    # command line argument
    if "--pretty" in sys.argv:
        sys.argv.remove("--pretty")
        indent = 4
    else:
        indent = 0

    # parse each statement in each script provided
    for a in sys.argv[1:]:
        with pathlib.Path(a).open() as f:
            for rq in sqlparse.split(f.read()):
                q = clean_query(rq)
                q = clean_functions(q)
                p = split_query(q)
                t = fetch_dependencies(p)

            # output
            sys.stdout.write(json.dumps(t, indent=indent if indent else None))
