"""Unit tests for :mod:`red_etl.io`."""

import ibis
import pandas as pd
import polars as pl
import pytest

from red_etl.backends.pandas import PandasBackend
from red_etl.backends.polars import PolarsBackend
from red_etl.io.csv import CSVSource, CSVSink
from red_etl.io.excel import ExcelSource, ExcelSink
from red_etl.io.parquet import ParquetSource, ParquetSink
from red_etl.io.sql import SQLSink, SQLSource


def test_csv_source_reads_with_custom_separator(tmp_path) -> None:
    """CSVSource should honor the separator parameter."""
    path = tmp_path / "data.csv"
    path.write_text("a;b\n1;hello\n2;world\n", encoding="utf-8")

    source = CSVSource(path, separator=";")
    table = source.read(PandasBackend())
    df = table.execute()

    assert isinstance(df, pd.DataFrame)
    assert df["a"].tolist() == [1, 2]
    assert df["b"].tolist() == ["hello", "world"]


def test_csv_source_reads_with_custom_encoding(tmp_path) -> None:
    """CSVSource should honor the encoding parameter."""
    path = tmp_path / "data.csv"
    path.write_text("name\nSão Paulo\n", encoding="latin1")

    source = CSVSource(path, encoding="latin1")
    table = source.read(PandasBackend())
    df = table.execute()

    assert df["name"].iloc[0] == "São Paulo"


def test_csv_source_reads_without_header(tmp_path) -> None:
    """CSVSource should read numeric columns when header=False."""
    path = tmp_path / "data.csv"
    path.write_text("1,hello\n2,world\n", encoding="utf-8")

    source = CSVSource(path, header=False)
    table = source.read(PandasBackend())
    df = table.execute()

    assert df.shape == (2, 2)


def test_csv_source_polars_backend(tmp_path) -> None:
    """CSVSource should return an Ibis table backed by Polars."""
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,hello\n2,world\n", encoding="utf-8")

    source = CSVSource(path)
    table = source.read(PolarsBackend())
    df = table.to_polars()

    assert isinstance(df, pl.DataFrame)
    assert df["a"].to_list() == [1, 2]


def test_csv_sink_writes_with_custom_separator(tmp_path) -> None:
    """CSVSink should write using the configured separator."""
    path = tmp_path / "output.csv"
    table = ibis.memtable({"a": [1, 2], "b": ["hello", "world"]})

    sink = CSVSink(path, separator=";")
    sink.write(table, PandasBackend())

    text = path.read_text(encoding="utf-8")
    assert ";" in text
    assert "hello" in text


def test_csv_sink_polars_backend(tmp_path) -> None:
    """CSVSink should write a Polars-backed Ibis table."""
    path = tmp_path / "output.csv"
    backend = PolarsBackend()
    table = backend.to_ibis_table(pl.DataFrame({"a": [1, 2], "b": ["hello", "world"]}))

    sink = CSVSink(path)
    sink.write(table, backend)

    text = path.read_text(encoding="utf-8")
    assert "hello" in text


def test_parquet_source_and_sink_round_trip_pandas(tmp_path) -> None:
    """ParquetSource and ParquetSink should round-trip through Ibis."""
    path = tmp_path / "data.parquet"
    original = ibis.memtable({"a": [1, 2], "b": ["hello", "world"]})

    ParquetSink(path).write(original, PandasBackend())
    table = ParquetSource(path).read(PandasBackend())
    df = table.execute()

    assert isinstance(df, pd.DataFrame)
    assert df["a"].tolist() == [1, 2]
    assert df["b"].tolist() == ["hello", "world"]


def test_parquet_source_and_sink_round_trip_polars(tmp_path) -> None:
    """ParquetSource and ParquetSink should round-trip through Ibis on Polars."""
    path = tmp_path / "data.parquet"
    backend = PolarsBackend()
    original = backend.to_ibis_table(pl.DataFrame({"a": [1, 2], "b": ["hello", "world"]}))

    ParquetSink(path).write(original, backend)
    table = ParquetSource(path).read(backend)
    df = table.to_polars()

    assert isinstance(df, pl.DataFrame)
    assert df["a"].to_list() == [1, 2]


def test_sql_source_reads_table(tmp_path) -> None:
    """SQLSource should read a table by name into an Ibis table."""
    path = tmp_path / "data.db"
    engine = f"sqlite:///{path}"
    original = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
    original.to_sql("users", engine, index=False)

    source = SQLSource(engine, table_name="users")
    table = source.read(PandasBackend())
    df = table.execute()

    assert df["id"].tolist() == [1, 2]
    assert df["name"].tolist() == ["Alice", "Bob"]


def test_sql_source_reads_query(tmp_path) -> None:
    """SQLSource should execute a raw query into an Ibis table."""
    path = tmp_path / "data.db"
    engine = f"sqlite:///{path}"
    original = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    original.to_sql("users", engine, index=False)

    source = SQLSource(engine, query="SELECT id FROM users WHERE id > 1")
    table = source.read(PandasBackend())
    df = table.execute()

    assert df["id"].tolist() == [2, 3]


def test_sql_sink_writes_table(tmp_path) -> None:
    """SQLSink should write an Ibis table to a SQL table."""
    path = tmp_path / "data.db"
    engine = f"sqlite:///{path}"
    table = ibis.memtable({"id": [1, 2], "name": ["Alice", "Bob"]})

    sink = SQLSink(engine, table_name="users_clean", if_exists="fail")
    sink.write(table, PandasBackend())

    result = pd.read_sql("SELECT * FROM users_clean", engine)
    assert result["id"].tolist() == [1, 2]


def test_sql_source_requires_query_or_table() -> None:
    """SQLSource should raise if neither query nor table_name is given."""
    with pytest.raises(ValueError, match="query' or 'table_name'"):
        SQLSource("sqlite:///test.db").read(PandasBackend())


def test_excel_source_reads_sheet(tmp_path) -> None:
    """ExcelSource should read a specific sheet into an Ibis table."""
    pytest.importorskip("openpyxl")
    path = tmp_path / "data.xlsx"
    original = pd.DataFrame({"a": [1, 2], "b": ["hello", "world"]})
    original.to_excel(path, sheet_name="Users", index=False)

    source = ExcelSource(path, sheet_name="Users")
    table = source.read(PandasBackend())
    df = table.execute()

    assert df["a"].tolist() == [1, 2]
    assert df["b"].tolist() == ["hello", "world"]


def test_excel_sink_writes_sheet(tmp_path) -> None:
    """ExcelSink should write an Ibis table to a named sheet."""
    pytest.importorskip("openpyxl")
    path = tmp_path / "output.xlsx"
    table = ibis.memtable({"a": [1, 2], "b": ["hello", "world"]})

    sink = ExcelSink(path, sheet_name="Users")
    sink.write(table, PandasBackend())

    result = pd.read_excel(path, sheet_name="Users")
    assert result["a"].tolist() == [1, 2]


def test_csv_source_returns_ibis_table(tmp_path) -> None:
    """CSVSource.read should return an Ibis Table, not a DataFrame."""
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,hello\n", encoding="utf-8")

    source = CSVSource(path)
    result = source.read(PandasBackend())

    assert isinstance(result, ibis.Table)


def test_csv_sink_accepts_ibis_table(tmp_path) -> None:
    """CSVSink.write should accept an Ibis Table."""
    path = tmp_path / "output.csv"
    table = ibis.memtable({"a": [1]})

    CSVSink(path).write(table, PandasBackend())

    text = path.read_text(encoding="utf-8")
    assert "a" in text


def test_source_unsupported_backend_raises(tmp_path) -> None:
    """CSVSource should raise for an unsupported backend."""
    path = tmp_path / "data.csv"
    path.write_text("a,b\n1,hello\n", encoding="utf-8")

    class FakeBackend:
        name = "fake"

    with pytest.raises(NotImplementedError):
        CSVSource(path).read(FakeBackend())


def test_sink_unsupported_backend_raises(tmp_path) -> None:
    """CSVSink should raise for an unsupported backend."""
    path = tmp_path / "output.csv"
    table = ibis.memtable({"a": [1]})

    class FakeBackend:
        name = "fake"

    with pytest.raises(NotImplementedError):
        CSVSink(path).write(table, FakeBackend())
