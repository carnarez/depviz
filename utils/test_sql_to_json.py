"""Some test regarding our little SQL parsing."""

from sql_to_json import clean_functions, clean_query, fetch_dependencies, split_query


def _process(query: str) -> dict[str, list[str]]:
    """Wrapper function to process a query.

    Parameters
    ----------
    query : str
        Query to process.

    Returns
    -------
    : dict[str, list[str]]
        Output of a processed query, to be asserted in the tests.
    """
    q = clean_query(query)
    q = clean_functions(q)
    s = split_query(q)
    d = fetch_dependencies(s)

    return q, s, d


def test_convoluted_query():
    """Test a convoluted query, including subqueries and subsubqueries.

    The following query contains:

    * subqueries defined through `WITH`,
    * subqueries within subqueries (...),
    * subqueries without `FROM` or `JOIN`,
    * a function including the `FROM` keyword,
    * `FROM`, `JOIN`, `UNION`.

    ```sql
    with
      subquery1 as (
        select
          attr1,
          attr2
        from (
          with
            subsubquery1 as (
              select
                t1.attr1,
                t2.attr2
              from table1 t1
              inner join table2 t2
              on t1.attr = t2.attr
            ),
            subsubquery2 as (
              select
                attr1,
                attr2
              from table3
            )
          select * from subsubquery1
          union all
          select * from subsubquery2
        )
        where attr1 <> 0
          and attr2 is not null
      ),
      subquery2 (
        select
          s1.*,
          t4.*
        from table4 t4
        left outer join subquery1 s1
        on t4.attr1 = s1.attr1 and t4.attr2 > 0
        inner join table5 t5
        on t4.attr1 = t5.attr1
        where t5.attr is not null
      ),
      subquery3 as (
        select
          trim('"' from attr1) as attr1,
          '2' as attr2
      )
    select
      s2.attr1,
      s2.attr2
    from subquery2 s2
    cross join subquery3 s3
    ```

    Below the query diagram:

    ```mermaid
    graph LR
      %% nodes
      node1(table1)
      node2(subsubquery1)
      node3(table2)
      node4(table3)
      node5(subsubquery2)
      node6(subquery1)
      node7(subquery2)
      node8(table4)
      node9(table5)
      node10(SELECT)
      node11(subquery3)
      %% links
      node1 --- node2
      node3 --- node2
      node4 --- node5
      node2 --- node6
      node5 --- node6
      node6 --- node7
      node8 --- node7
      node9 --- node7
      node7 --- node10
      node11 --- node10
      %% style
      linkStyle default fill:none,stroke-width:1px
    ```

    Note the final `SELECT` statement is indicated as a node in itself, despite not
    being an object.
    """
    q = """
    with
      subquery1 as (
        select
          attr1,
          attr2
        from (
          with
            subsubquery1 as (
              select
                t1.attr1,
                t2.attr2
              from table1 t1
              inner join table2 t2
              on t1.attr = t2.attr
            ),
            subsubquery2 as (
              select
                attr1,
                attr2
              from table3
            )
          select * from subsubquery1
          union all
          select * from subsubquery2
        )
        where attr1 <> 0
          and attr2 is not null
      ),
      subquery2 as (
        select
          s1.*,
          t4.*
        from table4 t4
        left outer join subquery1 s1
        on t4.attr1 = s1.attr1
        inner join table5 t5
        on t4.attr1 = t5.attr1
        where t5.attr is not null
      ),
      subquery3 as (
        select
          trim('"' from attr1) as attr1,
          '2' as attr2
      )
    select
      s2.attr1,
      s2.attr2
    from subquery2 s2
    cross join subquery3 s3
    """

    q, s, d = _process(q)

    assert d == {
        "subsubquery1": ["table1", "table2"],
        "subsubquery2": ["table3"],
        "subquery1": ["subsubquery1", "subsubquery2"],
        "subquery2": ["subquery1", "table4", "table5"],
        "subquery3": [],
        "SELECT": ["subquery2", "subquery3"],
    }


def test_create_external_table():
    """Test for the `CREATE EXTERNAL TABLE` and `LOCATION` statements.

    ```sql
    create external table external_table (
      attr1 timestamp,
      attr2 varchar(32),
      attr3 smallint
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
    STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat'
    OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
    LOCATION 's3://bucket/key/_symlink_format_manifest';
    ```
    """
    q = """
    CREATE EXTERNAL TABLE external_table (
      attr1 timestamp,
      attr2 varchar(32),
      attr3 smallint
    )
    ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
    STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat'
    OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
    LOCATION 's3://bucket/key/_symlink_format_manifest';
    """

    q, s, d = _process(q)

    assert d == {"external_table": ["s3://bucket/key/_symlink_format_manifest"]}


def test_create_materialized_view():
    """Test for `CREATE MATERIALIZED VIEW` statement.

    ```sql
    create materialized view materialized_view as (select * from external_table)
    ```

    ```sql
    create materialized view materialized_view
    backup no diststyle key distkey (attr) sortkey (attr1, attr2) as
    select * from external_table;
    ```
    """
    for q in (
        "create materialized view materialized_view as (select * from external_table)",
        " ".join(
            (
                "create materialized view materialized_view",
                "backup no diststyle key distkey (attr) sortkey (attr1, attr2) as",
                "select * from external_table;",
            )
        ),
    ):

        q, s, d = _process(q)

        assert d == {"materialized_view": ["external_table"]}


def test_create_table():
    """Test for `CREATE TABLE` statement.

    ```sql
    create table table2 as select * from table1
    ```
    """
    q, s, d = _process("create table table2 as select * from table1")

    assert s == {"table2": "create table table2 as select %COLUMNS% from table1"}
    assert d == {"table2": ["table1"]}


def test_create_view():
    """Test for `CREATE [OR REPLACE] VIEW` statements.

    ```sql
    create or replace view simple_view as select * from static_table
    ```

    ```sql
    create view simple_view as select * from static_table
    ```
    """
    for q in (
        "create or replace view simple_view as select * from static_table",
        "create view simple_view as select * from static_table",
    ):
        q, s, d = _process(q)

        assert d == {"simple_view": ["static_table"]}


def test_false_positive_from():
    """Test the exclusion of `..._from` attributes or `FUNCTION(... FROM ...)` clauses.

    ```sql
    select * from table t
    right join valid_from vf
    on t.attr = vf.attr and extract(month from vf.datetime) > 6
    ```

    ```sql
    select
      extract(year from datetime),
      extract(month from to_timestamp(trim('"' from string), 'YYYY-MM-DD HH:MI:SS.FF'))
    from table
    ```
    """
    # first
    q = """
    select * from table t
    right join valid_from vf
    on t.attr = vf.attr and extract(month from vf.datetime) > 6
    """

    q, s, d = _process(q)

    assert d == {"SELECT": ["table", "valid_from"]}

    # second
    q = """
    select
      extract(year from datetime),
      extract(month from to_timestamp(trim('"' from string), 'YYYY-MM-DD HH:MI:SS.FF'))
    from table
    """

    q, s, d = _process(q)

    assert s == {"SELECT": "select %COLUMNS% from table"}
    assert d == {"SELECT": ["table"]}


def test_subqueries():
    """Test for subqueries (CTE), _e.g._, statement including a `WITH` clause.

    ```sql
    with
      subquery1 as (
        select
          t1.attr1,
          t2.attr2
        from table1 t1
        inner join table2 t2
        on t1.attr = t2.attr
      ),
      subquery2 as (
        select
          attr1,
          attr2
        from table3
      )
    select * from subquery1 s1
    left join (select * from subquery2) s2
    on s1.attr1 = s2.attr1
    ```
    """
    q = """
    with
      subquery1 as (
        select
          t1.attr1,
          t2.attr2
        from table1 t1
        inner join table2 t2
        on t1.attr = t2.attr
      ),
      subquery2 as (
        select
          attr1,
          attr2
        from table3
      )
    select * from subquery1 s1
    left join (select * from subquery2) s2
    on s1.attr1 = s2.attr1
    """

    q, s, d = _process(q)

    assert d == {
        "subquery1": ["table1", "table2"],
        "subquery2": ["table3"],
        "SELECT": ["subquery1", "subquery2"],
    }
