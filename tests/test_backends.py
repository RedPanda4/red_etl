"""Unit tests for :mod:`red_etl.backends`."""

import ibis
import pandas as pd
import polars as pl
import pytest

from red_etl.backends.base import Backend
from red_etl.backends.pandas import PandasBackend
from red_etl.backends.polars import PolarsBackend


def test_backend_supports_native_returns_false_by_default() -> None:
    """A backend without overrides should not claim native support."""

    class DummyBackend(Backend):
        name = "dummy"

        def to_ibis_table(self, data):
            return ibis.memtable(data)

        def from_ibis_table(self, table):
            return table.execute()

    backend = DummyBackend()
    assert backend.supports_native(object()) is False


def test_backend_apply_native_raises_when_unsupported() -> None:
    """apply_native should raise when no override is registered."""

    class DummyBackend(Backend):
        name = "dummy"

        def to_ibis_table(self, data):
            return ibis.memtable(data)

        def from_ibis_table(self, table):
            return table.execute()

    backend = DummyBackend()
    with pytest.raises(KeyError):
        backend.apply_native(object(), None)


def test_pandas_backend_to_ibis_and_back() -> None:
    """PandasBackend should round-trip a DataFrame through Ibis."""
    data = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    backend = PandasBackend()

    table = backend.to_ibis_table(data)
    result = backend.from_ibis_table(table)

    assert isinstance(result, pd.DataFrame)
    assert result["a"].tolist() == [1, 2]


def test_pandas_backend_executes_ibis_expression() -> None:
    """PandasBackend should execute an Ibis mutate expression."""
    data = pd.DataFrame({"a": ["Alice", "Bob"], "b": ["Smith", "Jones"]})
    backend = PandasBackend()

    table = backend.to_ibis_table(data)
    expr = table.mutate(c=table.a + " " + table.b)
    result = backend.from_ibis_table(expr)

    assert result["c"].tolist() == ["Alice Smith", "Bob Jones"]


def test_polars_backend_to_ibis_and_back() -> None:
    """PolarsBackend should round-trip a Polars DataFrame through Ibis."""
    data = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    backend = PolarsBackend()

    table = backend.to_ibis_table(data)
    result = backend.from_ibis_table(table)

    assert isinstance(result, pl.DataFrame)
    assert result["a"].to_list() == [1, 2]


def test_polars_backend_executes_ibis_expression() -> None:
    """PolarsBackend should execute an Ibis mutate expression."""
    data = pl.DataFrame({"a": ["Alice", "Bob"], "b": ["Smith", "Jones"]})
    backend = PolarsBackend()

    table = backend.to_ibis_table(data)
    expr = table.mutate(c=table.a + " " + table.b)
    result = backend.from_ibis_table(expr)

    assert isinstance(result, pl.DataFrame)
    assert result["c"].to_list() == ["Alice Smith", "Bob Jones"]


def test_pandas_backend_has_builtin_native_overrides() -> None:
    """PandasBackend should register built-in native overrides."""
    from red_etl.transforms import ToNumeric, _ExplodeDictTransform, _ExplodeListTransform

    backend = PandasBackend()
    assert _ExplodeListTransform in backend.native_overrides
    assert _ExplodeDictTransform in backend.native_overrides
    assert ToNumeric in backend.native_overrides


def test_polars_backend_has_builtin_native_overrides() -> None:
    """PolarsBackend should register built-in native overrides."""
    from red_etl.transforms import ToNumeric, _ExplodeDictTransform, _ExplodeListTransform

    backend = PolarsBackend()
    assert _ExplodeListTransform in backend.native_overrides
    assert _ExplodeDictTransform in backend.native_overrides
    assert ToNumeric in backend.native_overrides
