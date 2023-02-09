# Module `csv_to_json`

Build an object -> upstream dependencies JSON object from CSV content.

**Parameters**

- \[`str`\]: Path to the CSV file(s).

**Returns**

- \[`str`\]: JSON-formatted, nested list of object and upstream dependencies (objects
  that are depended on).

**Usage**

```shell
$ python script.py <CSV FILE> [<CSV FILE> [...]]
```

**Example**

```shell
$ python script.py dependencies.csv
$ python script.py file1.csv file2.csv file3.csv
```

**Functions**

- [`convert_csv()`](#csv_to_jsonconvert_csv): Convert the CSV content to JSON.

## Functions

### `csv_to_json.convert_csv`

```python
convert_csv(content: str, objects: dict[str, list[str]]) -> tuple[str, list[str]]:
```

Convert the CSV content to JSON.

**Parameters**

- `content` \[`str`\]: The CSV content to parse and convert.
- `objects` \[`dict[str, list[str]]`\]: Dictionary of objects already parsed.

**Returns**

- \[`dict[str, list[str]]`\]: Updated dictionary of objects and upstream dependencies.

**Notes**

Expects a two columns dataset, each line embedding a `object1,object2` pair; the second
object is expected to be depended upon.

# Module `filter_json`

# Module `sql_to_json`

Extract upstream dependencies from SQL files, each containing a single query.

**Parameters**

- \[`str`\]: Path to the SQL script(s), each containing a _singled out_ SQL query.

**Returns**

- \[`str`\]: JSON-formatted, nested list of objects and associated list of upstream
  dependencies. One can see this object as child -> list of parents.

**Usage**

```shell
$ python script.py <SQL FILE> [<SQL FILE> [...]]
$ python script.py <SQL FILE> [<SQL FILE> [...]] --pretty
```

**Example**

```shell
$ python script.py view.sql --pretty
$ python script.py fact_*.sql dim_*.sql
```

**Note**

- Only a few SQL statements amongst the gazillions ways to write them are supported;
  feel free to drop a message with a new one to test.
- This is based on queries running on `Redshift`, no guarantees this would work on any
  other syntax (but `Redshift` is largely based on `PostgreSQL`, there's hope).
- This little stunt is still in alpha, and a lot more testing is required!

**Functions**

- [`clean_query()`](#sql_to_jsonclean_query): Deep-cleaning of a SQL query via
- [`split_query()`](#sql_to_jsonsplit_query): Split a query in its subqueries, if any.
- [`fetch_dependencies()`](#sql_to_jsonfetch_dependencies): Fetch upstream dependencies
  from each subquery.

## Functions

### `sql_to_json.clean_query`

```python
clean_query(query: str) -> str:
```

Deep-cleaning of a SQL query via [`sqlparse`](https://github.com/andialbrecht/sqlparse)
and regular expressions.

**Parameters**

- `query` \[`str`\]: The SQL query.

**Returns**

- \[`str`\]: Cleaned up query.

**Notes**

1. `sqlparse` tries to set all supported SQL statements to uppercase.
1. Further cleaning is done via the following regular expressions:
   - `"/\*.*\*/"` -> `""`: remove remaining multiline comments;
   - `"--.*"` -> `""`: remove remaining inline comments;
   - `"([(,)])"` -> `" , "`: single spaces around function parameters;
   - `"([A-Za-z0-9_]+)\s*\.\s*([A-Za-z0-9_]+)"` -> `"[...].[...]"`: remove spaces around
     object descriptors;
   - `"(.*)\s*=\s*(.*)"` -> `"[...] = [...]"`: single spaces around equal signs;
   - `"(.*)\s*\|\|\s*(.*)` -> `"[...] || [...]"`: single spaces around concatenation
     operators;
   - `"(.*)\s*::\s*(.*)"` -> `"[...]::[...]"`: remove spaces around datatyping
     operators;
   - `"[\s]+"` -> `" "`: replace multiple spaces by single spaces.

### `sql_to_json.split_query`

```python
split_query(query: str) -> dict[str, list[str]]:
```

Split a query in its subqueries, if any.

**Parameters**

- `query` \[`str`\]: The DDL to parse.

**Returns**

- \[`dict[str, list[str]]`\]: Dictionary of \[sub\]queries and associated DDL, split in
  parts if the `union` keyword is found.

**Notes**

Processing goes as follows:

1. Search for `... as ( select ... )` CTE statement via the `[^\s]+\s+AS\s+\(\s+SELECT`
   regular expression.
1. Read each character from there, keeping count of opening/closing brackets; once this
   number reaches zero (or we seeked to end of the query) we are done with the subquery.
1. Store the subquery (split on the `UNION` keyword, if any) under the CTE name.
1. Move on to the next subquery.
1. Extract the main query, if any, using the following regular expressions (these could
   be factored a bit further but clarity prevails):
   - `CREATE\s+EXTERNAL\s+TABLE\s+([^\s]+)`
   - `CREATE\s+TABLE\s([^\s]+)`
   - `CREATE\s+MATERIALIZED\s+VIEW\s([^\s]+)`
   - `CREATE\+OR\s+REPLACE\s+VIEW\s([^\s]+)`
   - `CREATE\s+VIEW\s([^\s]+)`

### `sql_to_json.fetch_dependencies`

```python
fetch_dependencies(parts: dict[str, list[str]]) -> dict[str, list[str]]:
```

Fetch upstream dependencies from each subquery.

**Parameters**

- \[`dict[str, list[str]]`\]: Dictionary of \[sub\]queries and associated DDL.

**Returns**

- \[`dict[str, list[str]]`\]: Dictionary of objects and associated list of upstream
  dependencies.

**Notes**

Supported regular expressions (_e.g._, SQL statements):

1. `FROM\s+([^\s(]+)`
1. `JOIN\s+([^\s(]+)`
1. `LOCATION\s+'(s3://.+)'` (`Redshift` stuff)
