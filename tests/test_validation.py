"""Unit tests for :mod:`red_etl.validation`."""

from __future__ import annotations

import ibis
import pandas as pd
import polars as pl
import pytest

from red_etl import Column, RedMeta
from red_etl.backends.pandas import PandasBackend
from red_etl.backends.polars import PolarsBackend
from red_etl.validation import (
    IbisPanderaValidator,
    PandasPanderaValidator,
    PolarsPanderaValidator,
    get_validator,
    register_validator,
    validate,
    validate_schema,
)
from red_etl.validation.base import _VALIDATOR_REGISTRY
from red_etl.validation.pandera.spark import SparkPanderaValidator


def _remove_backend(name: str) -> None:
    """Remove a backend entry from the global validator registry."""
    _VALIDATOR_REGISTRY.pop(name, None)


class User(RedMeta):
    """Simple schema used in validation tests."""

    id = Column(int, nullable=False)
    name = Column(str)
    score = Column(float)
    active = Column(bool)


class Event(RedMeta):
    """Schema with date/time types used in schema validation tests."""

    id = Column(int)
    created = Column("datetime")


def test_validate_schema_accepts_matching_ibis_table() -> None:
    """validate_schema should pass for a matching Ibis table."""
    table = ibis.memtable(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
        }
    )

    validate_schema(table, User)


def test_validate_schema_rejects_missing_column() -> None:
    """validate_schema should raise when a column is missing."""
    table = ibis.memtable({"id": [1, 2], "name": ["a", "b"], "score": [1.0, 2.0]})

    with pytest.raises(ValueError, match="missing columns"):
        validate_schema(table, User)


def test_validate_schema_rejects_extra_column() -> None:
    """validate_schema should raise when an extra column is present."""
    table = ibis.memtable(
        {
            "id": [1, 2],
            "name": ["a", "b"],
            "score": [1.0, 2.0],
            "active": [True, False],
            "extra": [1, 2],
        }
    )

    with pytest.raises(ValueError, match="extra columns"):
        validate_schema(table, User)


def test_validate_schema_rejects_wrong_type() -> None:
    """validate_schema should raise when a column type does not match."""
    table = ibis.memtable(
        {
            "id": ["a", "b"],
            "name": ["a", "b"],
            "score": [1.0, 2.0],
            "active": [True, False],
        }
    )

    with pytest.raises(ValueError, match="expected type"):
        validate_schema(table, User)


def test_validate_accepts_matching_pandas_dataframe() -> None:
    """A DataFrame that matches the schema should validate without errors."""
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
        }
    )

    result = validate(df, User)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["id", "name", "score", "active"]


def test_validate_accepts_matching_ibis_table() -> None:
    """An Ibis table that matches the schema should validate without errors."""
    table = ibis.memtable(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
        }
    )

    result = validate(table, User)

    # IbisPanderaValidator returns an Ibis table
    assert isinstance(result, ibis.Table)


def test_validate_with_pandas_backend_uses_native_pandera() -> None:
    """Passing PandasBackend should use pandera.pandas natively."""
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
        }
    )

    result = validate(df, User, backend=PandasBackend())

    assert isinstance(result, pd.DataFrame)


def test_validate_with_polars_backend_uses_native_pandera() -> None:
    """Passing PolarsBackend should validate a Polars DataFrame directly."""
    df = pl.DataFrame(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
        }
    )

    result = validate(df, User, backend=PolarsBackend())

    assert isinstance(result, pl.DataFrame)


def test_validate_rejects_missing_column() -> None:
    """A DataFrame missing a schema column should raise a schema error."""
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            # "active" is missing
        }
    )

    with pytest.raises(Exception):
        validate(df, User)


def test_validate_rejects_extra_column() -> None:
    """A DataFrame with extra columns should raise a schema error."""
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
            "extra": [1, 2],
        }
    )

    with pytest.raises(Exception):
        validate(df, User)


def test_validate_rejects_wrong_type() -> None:
    """A DataFrame with a wrong column type should raise a schema error."""
    df = pd.DataFrame(
        {
            "id": ["a", "b"],  # should be int
            "name": ["alice", "bob"],
            "score": [1.5, 2.5],
            "active": [True, False],
        }
    )

    with pytest.raises(Exception):
        validate(df, User)


def test_pandas_validator_from_schema_returns_schema() -> None:
    """from_schema should return the built Pandera DataFrameSchema."""
    validator = PandasPanderaValidator()

    schema = validator.from_schema(User)

    assert schema is not None
    assert "id" in schema.columns
    assert "name" in schema.columns


def test_pandas_validator_validate_without_from_schema_raises() -> None:
    """validate should raise if from_schema has not been called."""
    validator = PandasPanderaValidator()
    df = pd.DataFrame({"id": [1], "name": ["a"], "score": [1.0], "active": [True]})

    with pytest.raises(RuntimeError, match="from_schema"):
        validator.validate(df)


def test_get_validator_returns_backend_specific_instance() -> None:
    """get_validator should return the right validator for a backend."""
    assert isinstance(get_validator(PandasBackend()), PandasPanderaValidator)
    assert isinstance(get_validator(PolarsBackend()), PolarsPanderaValidator)


def test_get_validator_unsupported_backend_raises() -> None:
    """A backend without a registered validator should raise clearly."""

    class FakeBackend:
        name = "spark"

    with pytest.raises(NotImplementedError, match="spark"):
        get_validator(FakeBackend())  # type: ignore[arg-type]


def test_register_validator_allows_pandera_override() -> None:
    """register_validator should let users add or replace Pandera validators."""

    class CustomValidator(PandasPanderaValidator):
        pass

    register_validator("custom", CustomValidator)
    try:

        class FakeBackend:
            name = "custom"

        validator = get_validator(FakeBackend())  # type: ignore[arg-type]
        assert isinstance(validator, CustomValidator)
    finally:
        _remove_backend("custom")


def test_register_validator_accepts_non_pandera_validator() -> None:
    """The registry is generic: non-Pandera validators can be registered."""
    from red_etl.validation.base import Validator

    class DummyValidator(Validator):
        def from_schema(self, schema: type[RedMeta]) -> object:
            return object()

        def validate(self, data: object) -> object:
            return data

    register_validator("dummy", DummyValidator)
    try:

        class FakeBackend:
            name = "dummy"

        validator = get_validator(FakeBackend())  # type: ignore[arg-type]
        assert isinstance(validator, DummyValidator)
    finally:
        _remove_backend("dummy")


def test_register_validator_rejects_non_subclass() -> None:
    """register_validator should reject classes that are not validators."""

    class NotAValidator:
        pass

    with pytest.raises(TypeError):
        register_validator("bad", NotAValidator)  # type: ignore[arg-type]


def test_pandas_validator_maps_python_types() -> None:
    """PandasPanderaValidator should map common Python types."""
    import pandera.pandas as pa

    validator = PandasPanderaValidator()
    assert validator.map_dtype(int) is pa.Int
    assert validator.map_dtype(str) is pa.String
    assert validator.map_dtype(float) is pa.Float
    assert validator.map_dtype(bool) is pa.Bool


def test_polars_validator_maps_python_types() -> None:
    """PolarsPanderaValidator should map common Python types to Polars dtypes."""
    validator = PolarsPanderaValidator()
    assert validator.map_dtype(int) is pl.Int64
    assert validator.map_dtype(str) is pl.Utf8
    assert validator.map_dtype(float) is pl.Float64
    assert validator.map_dtype(bool) is pl.Boolean


def test_ibis_validator_maps_python_types() -> None:
    """IbisPanderaValidator should map common Python types to Ibis dtypes."""
    validator = IbisPanderaValidator()
    assert validator.map_dtype(int) == ibis.dtype("int64")
    assert validator.map_dtype(str) == ibis.dtype("string")


def test_spark_validator_is_placeholder() -> None:
    """SparkPanderaValidator should be a placeholder that raises on use."""
    validator = SparkPanderaValidator()

    with pytest.raises(NotImplementedError):
        validator.from_schema(User)
