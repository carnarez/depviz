# Module `csv_to_json`

Extract objects and their parents from SQL statements.

**Parameters**

- \[`str`\]: Path to the CSV file.

**Returns**

- \[`str`\]: JSON-formatted, nested list of object and dependencies.

**Usage**

```shell
$ python script.py <CSV FILE> [<CSV FILE> [...]]
```

**Example**

```shell
$ python script.py dependencies.sql
$ python script.py deps-dev.csv deps-prd.csv
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
- `objects` \[`dict[str, list[str]]`\]: List of objects and parents already parsed.

**Returns**

- \[`dict[str, list[str]]`\]: Updated list of objects and children.

**Notes**

Expects a two columns dataset, each line embedding a `child,parent` pair.

# Module `sql_to_json`

Extract objects and their parents from SQL statements.

**Parameters**

- \[`str`\]: Path to the SQL script, containing more than one SQL statement.

**Returns**

- \[`str`\]: JSON-formatted, nested list of object and dependencies.

**Usage**

```shell
$ python script.py <SQL FILE> [<SQL FILE> [...]]
```

**Example**

```shell
$ python script.py views.sql
$ python script.py fact_*.sql dim_*.sql
```

**Functions**

- [`clean_query()`](#sql_to_jsonclean_query): Deep-cleaning of a SQL query via
- [`fetch_objects()`](#sql_to_jsonfetch_objects): Extract materialized view object and
  its dependencies from a SQL statement.

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

### `sql_to_json.fetch_objects`

```python
fetch_objects(query: str, objects: dict[str, list[str]]) -> tuple[str, list[str]]:
```

Extract materialized view object and its dependencies from a SQL statement.

**Parameters**

- `query` \[`str`\]: The DDL to parse.
- `objects` \[`dict[str, list[str]]`\]: List of objects and parents already parsed.

**Returns**

- \[`dict[str, list[str]]`\]: Updated list of objects and children.

**Notes**

1. Only materialized views are checked.
1. Supported SQL statements and associated regular expressions:
   - \`CREATE\\s+\[A-Za-z\]*\\s+MATERIALIZED\\s+VIEW\\s+(\[^(\].*?)\\s\`\`
   - `FROM\s+(\S+rated\.[^(\s;)]+)`
   - `JOIN\s+(\S+rated\.[^(\s;)]+)`
