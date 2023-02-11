"""Some test regarding our little SQL parsing."""

from sql_to_json import clean_query, fetch_dependencies, split_query


def test_convoluted_query():
    """Test a convoluted query, including subqueries and subsubqueries.

    The following query contains:

    * subqueries defined through `WITH`,
    * subqueries within subqueries (...),
    * subqueries without `FROM` or `JOIN`,
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
          '1' as attr1,
          '2' as attr2
      )
    select
      s1.attr1,
      s2.attr2
    from subquery1 s1
    join subquery2 s2
    on s1.attr = s2.attr
    cross join subquery3
    ```
    """
    # query
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
          '1' as attr1,
          '2' as attr2
      )
    select
      s1.attr1,
      s2.attr2
    from subquery1 s1
    join subquery2 s2
    on s1.attr = s2.attr
    cross join subquery3
    """

    # process
    q = clean_query(q)
    s = split_query(q)
    d = fetch_dependencies(s)

    # test
    assert d == {
        "subsubquery1": ["table1", "table2"],
        "subsubquery2": ["table3"],
        "subquery1": ["subsubquery1", "subsubquery2"],
        "subquery2": ["subquery1", "table4", "table5"],
        "subquery3": [],
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
    # query
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

    # process
    q = clean_query(q)
    s = split_query(q)
    d = fetch_dependencies(s)

    # test
    assert d == {"external_table": ["s3://bucket/key/_symlink_format_manifest"]}


def test_create_materialized_view():
    """Test for `CREATE MATERIALIZED VIEW` statement.

    ```sql
    create materialized view materialized_view
    backup no diststyle key distkey (attr) sortkey (attr1, attr2) as
    select * from external_table
    ```
    """
    # query
    q = """
    create materialized view materialized_view
    backup no diststyle key distkey (attr) sortkey (attr1, attr2) as
    select * from external_table
    """

    # process
    q = clean_query(q)
    s = split_query(q)
    d = fetch_dependencies(s)

    # test
    assert d == {"materialized_view": ["external_table"]}


def test_create_table():
    """Test for `CREATE TABLE` statement.

    ```sql
    create table table2 as select * from table1
    ```
    """
    # query
    q = "create table table2 as select * from table1"

    # process
    q = clean_query(q)
    s = split_query(q)
    d = fetch_dependencies(s)

    # tests
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
    # queries
    for q in (
        "create or replace view simple_view as select * from static_table",
        "create view simple_view as select * from static_table",
    ):

        # process
        q = clean_query(q)
        s = split_query(q)
        d = fetch_dependencies(s)

        # test
        assert d == {"simple_view": ["static_table"]}
