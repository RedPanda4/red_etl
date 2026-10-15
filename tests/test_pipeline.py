"""Unit tests for :mod:`red_etl.pipeline`."""

import ibis
import pandas as pd
import polars as pl
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
    ToDateTime,
    ToNumeric,
    apply_transforms,
)
from red_etl.backends.pandas import PandasBackend
from red_etl.backends.polars import PolarsBackend


def _user_schema() -> type[RedMeta]:
    """Return a RedMeta schema with a single concatenation transform."""

    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)
        full_name = Column(
            str,
            transform=ConcatColumns([first_name, last_name], separator=" "),
        )

    return User


def test_apply_transforms_pandas_adds_calculated_column() -> None:
    """apply_transforms should execute transforms on the Pandas backend."""
    User = _user_schema()
    table = ibis.memtable(
        {
            "first_name": ["Alice", "Bob"],
            "last_name": ["Smith", "Jones"],
        }
    )

    result = apply_transforms(table, User, PandasBackend())
    df = result.execute()

    assert isinstance(df, pd.DataFrame)
    assert "full_name" in df.columns
    assert df["full_name"].tolist() == ["Alice Smith", "Bob Jones"]


def test_apply_transforms_polars_adds_calculated_column() -> None:
    """apply_transforms should execute transforms on the Polars backend."""
    User = _user_schema()
    backend = PolarsBackend()
    table = backend.to_ibis_table(
        pl.DataFrame(
            {
                "first_name": ["Alice", "Bob"],
                "last_name": ["Smith", "Jones"],
            }
        )
    )

    result = apply_transforms(table, User, backend)
    df = result.to_polars()

    assert isinstance(df, pl.DataFrame)
    assert "full_name" in df.columns
    assert df["full_name"].to_list() == ["Alice Smith", "Bob Jones"]


def test_apply_transforms_leaves_untransformed_columns_intact() -> None:
    """apply_transforms should not modify columns without a transform."""
    User = _user_schema()
    table = ibis.memtable(
        {
            "first_name": ["Alice"],
            "last_name": ["Smith"],
        }
    )

    result = apply_transforms(table, User, PandasBackend())
    df = result.execute()

    assert df["first_name"].tolist() == ["Alice"]
    assert df["last_name"].tolist() == ["Smith"]


def test_apply_transforms_returns_original_when_no_transforms() -> None:
    """apply_transforms should return the table unchanged if no transforms exist."""

    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)

    table = ibis.memtable(
        {
            "first_name": ["Alice"],
            "last_name": ["Smith"],
        }
    )

    result = apply_transforms(table, User, PandasBackend())
    df = result.execute()

    assert "full_name" not in df.columns
    assert df["first_name"].tolist() == ["Alice"]


def test_apply_transforms_uses_native_override_when_registered() -> None:
    """apply_transforms should split the plan when a native override exists."""

    class Uppercase(ConcatColumns):
        """Dummy transform used to test native override routing."""

    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)
        full_name = Column(
            str,
            transform=Uppercase([first_name, last_name], separator=" "),
        )

    def native_uppercase(transform: ConcatColumns, data: pd.DataFrame) -> pd.DataFrame:
        data[transform.output_column] = (
            data["first_name"] + transform.separator + data["last_name"]
        ).str.upper()
        return data

    backend = PandasBackend()
    backend.native_overrides[Uppercase] = native_uppercase

    table = ibis.memtable(
        {
            "first_name": ["Alice"],
            "last_name": ["Smith"],
        }
    )

    result = apply_transforms(table, User, backend)
    df = result.execute()

    assert df["full_name"].tolist() == ["ALICE SMITH"]


def test_apply_transforms_returns_ibis_table() -> None:
    """apply_transforms should return an Ibis Table."""
    User = _user_schema()
    table = ibis.memtable(
        {
            "first_name": ["Alice"],
            "last_name": ["Smith"],
        }
    )

    result = apply_transforms(table, User, PandasBackend())

    assert isinstance(result, ibis.Table)


def test_apply_transforms_accepts_pandas_dataframe() -> None:
    """apply_transforms should accept a Pandas DataFrame and convert it."""
    User = _user_schema()
    data = pd.DataFrame(
        {
            "first_name": ["Alice", "Bob"],
            "last_name": ["Smith", "Jones"],
        }
    )

    result = apply_transforms(data, User, PandasBackend())

    assert isinstance(result, ibis.Table)
    assert result.execute()["full_name"].tolist() == ["Alice Smith", "Bob Jones"]


def test_apply_transforms_accepts_polars_dataframe() -> None:
    """apply_transforms should accept a Polars DataFrame and convert it."""
    User = _user_schema()
    backend = PolarsBackend()
    data = pl.DataFrame(
        {
            "first_name": ["Alice", "Bob"],
            "last_name": ["Smith", "Jones"],
        }
    )

    result = apply_transforms(data, User, backend)

    assert isinstance(result, ibis.Table)
    assert result.to_polars()["full_name"].to_list() == ["Alice Smith", "Bob Jones"]


def test_apply_transforms_to_datetime_pandas() -> None:
    """ToDateTime should parse strings on the Pandas backend."""

    class Event(RedMeta):
        ts_str = Column(str)
        ts = Column("datetime", transform=ToDateTime(ts_str, "%Y-%m-%d %H:%M:%S"))

    table = ibis.memtable({"ts_str": ["2024-01-15 10:30:00"]})
    result = apply_transforms(table, Event, PandasBackend())
    df = result.execute()

    assert df["ts"][0].year == 2024
    assert df["ts"][0].month == 1
    assert df["ts"][0].day == 15


def test_apply_transforms_to_bool_pandas() -> None:
    """ToBool should map strings to booleans on the Pandas backend."""

    class User(RedMeta):
        active_str = Column(str)
        active = Column(bool, transform=ToBool(active_str))

    table = ibis.memtable({"active_str": ["1", "0", "true", "false", "maybe"]})
    result = apply_transforms(table, User, PandasBackend())
    df = result.execute()

    assert df["active"].tolist()[:4] == [True, False, True, False]
    assert pd.isna(df["active"].iloc[4])


def test_apply_transforms_to_numeric_pandas() -> None:
    """ToNumeric should cast strings to numbers on the Pandas backend."""

    class Product(RedMeta):
        price_str = Column(str)
        price = Column(float, transform=ToNumeric(price_str, "float64"))

    table = ibis.memtable({"price_str": ["10.5", "20.25"]})
    result = apply_transforms(table, Product, PandasBackend())
    df = result.execute()

    assert df["price"].tolist() == [10.5, 20.25]


def test_apply_transforms_regex_extract_pandas() -> None:
    """RegexExtract should extract patterns on the Pandas backend."""

    class Log(RedMeta):
        message = Column(str)
        error_code = Column(str, transform=RegexExtract(message, r"ERROR-(\d+)", group=1))

    table = ibis.memtable({"message": ["ERROR-123", "ERROR-456"]})
    result = apply_transforms(table, Log, PandasBackend())
    df = result.execute()

    assert df["error_code"].tolist() == ["123", "456"]


def test_apply_transforms_explode_list_pandas() -> None:
    """ExplodeList should extract list elements on the Pandas backend."""

    class Order(RedMeta):
        items = Column("array")
        item_0, item_1 = ExplodeList(
            items,
            outputs=[
                OutputField("item_0", str),
                OutputField("item_1", str),
            ],
        )

    table = ibis.memtable({"items": [["a", "b"], ["c", "d"]]})
    result = apply_transforms(table, Order, PandasBackend())
    df = result.execute()

    assert df["item_0"].tolist() == ["a", "c"]
    assert df["item_1"].tolist() == ["b", "d"]


def test_apply_transforms_explode_list_raises_on_wrong_length() -> None:
    """ExplodeList should raise when a list has the wrong length."""

    class Order(RedMeta):
        items = Column("array")
        item_0, item_1 = ExplodeList(
            items,
            outputs=[
                OutputField("item_0", str),
                OutputField("item_1", str),
            ],
        )

    table = ibis.memtable({"items": [["a", "b"], ["c"]]})

    with pytest.raises(ValueError, match="Expected list of length"):
        apply_transforms(table, Order, PandasBackend())


def test_apply_transforms_explode_dict_pandas() -> None:
    """ExplodeDict should extract dictionary values on the Pandas backend."""

    class Order(RedMeta):
        raw = Column("map")
        col_a, col_b = ExplodeDict(
            raw,
            outputs=[
                OutputField("col_a", int, source_key="a"),
                OutputField("col_b", int, source_key="b"),
            ],
        )

    table = ibis.memtable({"raw": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]})
    result = apply_transforms(table, Order, PandasBackend())
    df = result.execute()

    assert df["col_a"].tolist() == [1, 3]
    assert df["col_b"].tolist() == [2, 4]


def test_apply_transforms_explode_dict_missing_key_to_null() -> None:
    """ExplodeDict should insert null for missing keys when on_missing='null'."""

    class Order(RedMeta):
        raw = Column("map")
        col_a, col_b = ExplodeDict(
            raw,
            outputs=[
                OutputField("col_a", int, source_key="a"),
                OutputField("col_b", int, source_key="b"),
            ],
        )

    table = ibis.memtable({"raw": [{"a": 1}, {"b": 2}]})
    result = apply_transforms(table, Order, PandasBackend())
    df = result.execute()

    assert df["col_a"].tolist()[0] == 1
    assert pd.isna(df["col_a"].iloc[1])
    assert pd.isna(df["col_b"].iloc[0])
    assert df["col_b"].tolist()[1] == 2


def test_apply_transforms_explode_dict_missing_key_raises() -> None:
    """ExplodeDict should raise for missing keys when on_missing='raise'."""

    class Order(RedMeta):
        raw = Column("map")
        col_a, = ExplodeDict(
            raw,
            outputs=[OutputField("col_a", int, source_key="a")],
            on_missing="raise",
        )

    table = ibis.memtable({"raw": [{"b": 1}]})

    with pytest.raises(KeyError):
        apply_transforms(table, Order, PandasBackend())


def test_apply_transforms_to_numeric_coerce_pandas() -> None:
    """ToNumeric with errors='coerce' should produce null for invalid values."""

    class Product(RedMeta):
        price_str = Column(str)
        price = Column(float, transform=ToNumeric(price_str, "float64", errors="coerce"))

    table = ibis.memtable({"price_str": ["10.5", "bad", "20.25"]})
    result = apply_transforms(table, Product, PandasBackend())
    df = result.execute()

    assert df["price"].tolist()[0] == 10.5
    assert pd.isna(df["price"].iloc[1])
    assert df["price"].tolist()[2] == 20.25


def test_apply_transforms_regex_extract_returns_null_on_polars() -> None:
    """RegexExtract should return null on non-match for Polars backend too."""

    class Log(RedMeta):
        message = Column(str)
        error_code = Column(str, transform=RegexExtract(message, r"ERROR-(\d+)", group=1))

    backend = PolarsBackend()
    table = backend.to_ibis_table(pl.DataFrame({"message": ["ERROR-123", "BAD", ""]}))
    result = apply_transforms(table, Log, backend)
    df = result.to_polars()

    assert df["error_code"].to_list()[0] == "123"
    assert df["error_code"].to_list()[1] is None
    assert df["error_code"].to_list()[2] is None


def test_apply_transforms_explode_list_polars() -> None:
    """ExplodeList should work on Polars backend with strict length check."""

    class Order(RedMeta):
        items = Column("array")
        item_0, item_1 = ExplodeList(
            items,
            outputs=[
                OutputField("item_0", str),
                OutputField("item_1", str),
            ],
        )

    backend = PolarsBackend()
    table = backend.to_ibis_table(pl.DataFrame({"items": [["a", "b"], ["c", "d"]]}))
    result = apply_transforms(table, Order, backend)
    df = result.to_polars()

    assert df["item_0"].to_list() == ["a", "c"]
    assert df["item_1"].to_list() == ["b", "d"]


def test_apply_transforms_to_numeric_coerce_polars() -> None:
    """ToNumeric with errors='coerce' should work on Polars backend."""

    class Product(RedMeta):
        price_str = Column(str)
        price = Column(float, transform=ToNumeric(price_str, "float64", errors="coerce"))

    backend = PolarsBackend()
    table = backend.to_ibis_table(pl.DataFrame({"price_str": ["10.5", "bad", "20.25"]}))
    result = apply_transforms(table, Product, backend)
    df = result.to_polars()

    assert df["price"].to_list()[0] == 10.5
    assert df["price"].to_list()[1] is None
    assert df["price"].to_list()[2] == 20.25


@pytest.mark.parametrize("backend", [PandasBackend(), PolarsBackend()])
def test_apply_transforms_same_schema_on_multiple_backends(backend) -> None:
    """The same RedMeta schema should run on every supported backend."""
    User = _user_schema()

    if isinstance(backend, PandasBackend):
        table = ibis.memtable(
            {"first_name": ["Alice", "Bob"], "last_name": ["Smith", "Jones"]}
        )
        full_names = apply_transforms(table, User, backend).execute()["full_name"].tolist()
    else:
        table = backend.to_ibis_table(
            pl.DataFrame(
                {"first_name": ["Alice", "Bob"], "last_name": ["Smith", "Jones"]}
            )
        )
        full_names = apply_transforms(table, User, backend).to_polars()["full_name"].to_list()

    assert full_names == ["Alice Smith", "Bob Jones"]
