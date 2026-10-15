"""Unit tests for :mod:`red_etl.transforms`."""

import datetime

import ibis
import pandas as pd
import pytest

from red_etl import (
    Column,
    ConcatColumns,
    ExplodeDict,
    ExplodeList,
    OutputField,
    RedMeta,
    RegexExtract,
    ToBool,
    ToDate,
    ToDateTime,
    ToNumeric,
)
from red_etl.transforms import _column_name, _ExplodeDictTransform, _ExplodeListTransform


def test_concat_columns_stores_configuration() -> None:
    """ConcatColumns should store columns, separator and output name."""
    transform = ConcatColumns(["a", "b"], separator="-", output="c")

    assert transform.input_columns() == ["a", "b"]
    assert transform.separator == "-"
    assert transform.output_column == "c"


def test_concat_columns_accepts_column_descriptors() -> None:
    """ConcatColumns should resolve Column descriptors to their names."""

    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)

    transform = ConcatColumns([User.first_name, User.last_name], output="full_name")

    assert transform.input_columns() == ["first_name", "last_name"]
    assert transform.output_column == "full_name"


def test_concat_columns_output_name_inferred_by_redmeta() -> None:
    """When owned by a Column, RedMeta should set the transform output name."""

    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)
        full_name = Column(
            str,
            transform=ConcatColumns([first_name, last_name], separator=" "),
        )

    column = User.columns()["full_name"]
    assert column.transform is not None
    assert column.transform.output_column == "full_name"


def test_concat_columns_explicit_output_name_preserved() -> None:
    """An explicitly provided output name should not be overwritten."""

    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)
        full_name = Column(
            str,
            transform=ConcatColumns(
                [first_name, last_name],
                separator=" ",
                output="complete_name",
            ),
        )

    column = User.columns()["full_name"]
    assert column.transform.output_column == "complete_name"


def test_concat_columns_to_ibis() -> None:
    """ConcatColumns.to_ibis should produce a table with the new column."""
    transform = ConcatColumns(["first_name", "last_name"], separator=" ", output="full_name")
    table = ibis.memtable(
        {"first_name": ["Alice", "Bob"], "last_name": ["Smith", "Jones"]}
    )

    result = transform.to_ibis(table)
    df = result.execute()

    assert "full_name" in df.columns
    assert df["full_name"].tolist() == ["Alice Smith", "Bob Jones"]


def test_concat_columns_to_ibis_single_column() -> None:
    """ConcatColumns with a single column should copy that column."""
    transform = ConcatColumns(["first_name"], output="only_name")
    table = ibis.memtable({"first_name": ["Alice", "Bob"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["only_name"].tolist() == ["Alice", "Bob"]


def test_concat_columns_requires_at_least_one_column() -> None:
    """ConcatColumns should raise when initialized with no columns."""
    with pytest.raises(ValueError, match="at least one column"):
        ConcatColumns([])


def test_to_date_to_ibis() -> None:
    """ToDate.to_ibis should parse strings to dates."""
    transform = ToDate("date_str", "%Y-%m-%d", output="date")
    table = ibis.memtable({"date_str": ["2024-01-15", "2024-02-20"]})

    result = transform.to_ibis(table)
    df = result.execute()

    dates = df["date"].dt.date.tolist()
    assert dates == [datetime.date(2024, 1, 15), datetime.date(2024, 2, 20)]


def test_to_datetime_to_ibis() -> None:
    """ToDateTime.to_ibis should parse strings to timestamps."""
    transform = ToDateTime("ts_str", "%Y-%m-%d %H:%M:%S", output="ts")
    table = ibis.memtable({"ts_str": ["2024-01-15 10:30:00"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["ts"][0].year == 2024
    assert df["ts"][0].month == 1
    assert df["ts"][0].day == 15


def test_to_bool_to_ibis_default_values() -> None:
    """ToBool.to_ibis should map default true/false strings."""
    transform = ToBool("active_str", output="active")
    table = ibis.memtable({"active_str": ["1", "0", "true", "false", "yes", "no", "maybe"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["active"].tolist()[:6] == [True, False, True, False, True, False]
    assert pd.isna(df["active"].iloc[6])


def test_to_bool_to_ibis_custom_values() -> None:
    """ToBool.to_ibis should honor custom true/false values."""
    transform = ToBool("flag", true_values=["Y"], false_values=["N"], output="flag_bool")
    table = ibis.memtable({"flag": ["Y", "N", "?"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["flag_bool"].tolist()[:2] == [True, False]
    assert pd.isna(df["flag_bool"].iloc[2])


def test_to_numeric_to_ibis_int() -> None:
    """ToNumeric.to_ibis should cast strings to integers."""
    transform = ToNumeric("num_str", dtype="int64", output="num")
    table = ibis.memtable({"num_str": ["1", "2", "3"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["num"].tolist() == [1, 2, 3]


def test_to_numeric_to_ibis_float() -> None:
    """ToNumeric.to_ibis should cast strings to floats."""
    transform = ToNumeric("price_str", dtype="float64", output="price")
    table = ibis.memtable({"price_str": ["10.5", "20.25"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["price"].tolist() == [10.5, 20.25]


def test_regex_extract_to_ibis_group_one() -> None:
    """RegexExtract.to_ibis should extract a capture group and return null on mismatch."""
    transform = RegexExtract("message", r"ERROR-(\d+)", group=1, output="error_code")
    table = ibis.memtable({"message": ["ERROR-123", "ERROR-456", "OK", ""]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["error_code"].tolist()[:2] == ["123", "456"]
    assert pd.isna(df["error_code"].iloc[2])
    assert pd.isna(df["error_code"].iloc[3])


def test_regex_extract_to_ibis_group_zero() -> None:
    """RegexExtract.to_ibis with group=0 should return the full match or null."""
    transform = RegexExtract("message", r"ERROR-\d+", group=0, output="match")
    table = ibis.memtable({"message": ["ERROR-123", "ERROR-456", "OK"]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["match"].tolist()[:2] == ["ERROR-123", "ERROR-456"]
    assert pd.isna(df["match"].iloc[2])


def test_explode_list_to_ibis_extracts_elements() -> None:
    """ExplodeList.to_ibis should extract list elements into columns."""
    columns = ExplodeList(
        "items",
        outputs=[
            OutputField("item_0", str),
            OutputField("item_1", str),
        ],
    )
    transform = columns[0].transform
    assert isinstance(transform, _ExplodeListTransform)
    table = ibis.memtable({"items": [["a", "b"], ["c", "d"]]})

    result = transform.to_ibis(table)
    df = result.execute()

    assert df["item_0"].tolist() == ["a", "c"]
    assert df["item_1"].tolist() == ["b", "d"]


def test_explode_list_returns_columns_for_unpacking() -> None:
    """ExplodeList should return a tuple of Column descriptors."""
    item_0, item_1 = ExplodeList(
        "items",
        outputs=[
            OutputField("item_0", str),
            OutputField("item_1", int),
        ],
    )

    assert item_0.name == "item_0"
    assert item_0.dtype is str
    assert item_0.transform is not None

    assert item_1.name == "item_1"
    assert item_1.dtype is int
    assert item_1.transform is None


def test_explode_list_requires_at_least_one_output() -> None:
    """ExplodeList should raise when initialized with no outputs."""
    with pytest.raises(ValueError, match="at least one OutputField"):
        ExplodeList("items", outputs=[])


def test_explode_dict_to_ibis_requires_native_override() -> None:
    """ExplodeDict.to_ibis should raise because it needs a native override."""
    columns = ExplodeDict(
        "raw",
        outputs=[OutputField("col_a", int)],
    )
    transform = columns[0].transform
    assert isinstance(transform, _ExplodeDictTransform)
    table = ibis.memtable({"raw": [{"a": 1}]})

    with pytest.raises(NotImplementedError):
        transform.to_ibis(table)


def test_explode_dict_returns_columns_for_unpacking() -> None:
    """ExplodeDict should return a tuple of Column descriptors."""
    col_a, col_b = ExplodeDict(
        "raw",
        outputs=[
            OutputField("col_a", int),
            OutputField("col_b", int, source_key="b"),
        ],
    )

    assert col_a.name == "col_a"
    assert col_a.dtype is int
    assert col_a.transform is not None

    assert col_b.name == "col_b"
    assert col_b.dtype is int
    assert col_b.transform is None


def test_explode_dict_requires_at_least_one_mapping() -> None:
    """ExplodeDict should raise when initialized with an empty mapping."""
    with pytest.raises(ValueError, match="at least one OutputField"):
        ExplodeDict("raw", outputs=[])


def test_explode_dict_validates_on_missing() -> None:
    """ExplodeDict should validate the on_missing parameter."""
    with pytest.raises(ValueError, match="on_missing must be"):
        ExplodeDict(
            "raw",
            outputs=[OutputField("col_a", int)],
            on_missing="ignore",
        )


def test_to_numeric_validates_errors_parameter() -> None:
    """ToNumeric should validate the errors parameter."""
    with pytest.raises(ValueError, match="errors must be"):
        ToNumeric("s", errors="bad")


def test_column_name_resolves_string() -> None:
    """_column_name should return a plain string unchanged."""
    assert _column_name("foo") == "foo"


def test_column_name_resolves_column_descriptor() -> None:
    """_column_name should return the name of a Column descriptor."""

    class User(RedMeta):
        id = Column(int)

    assert _column_name(User.id) == "id"


def test_column_name_rejects_invalid_type() -> None:
    """_column_name should raise TypeError for unsupported inputs."""
    with pytest.raises(TypeError):
        _column_name(123)  # type: ignore[arg-type]
