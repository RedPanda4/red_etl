"""Polars-native Pandera validator."""

from __future__ import annotations

from typing import Any

import ibis
import pandera.polars as pa
import polars as pl

from red_etl.validation.pandera.base import BasePanderaValidator


class PolarsPanderaValidator(BasePanderaValidator):
    """Validate Polars DataFrames using ``pandera.polars``."""

    @property
    def pandera_module(self) -> Any:
        """Return ``pandera.polars``."""
        return pa

    def map_dtype(self, dtype: type | str) -> Any:
        """Map a ``Column.dtype`` to a Polars data type."""
        mapping: dict[type | str, Any] = {
            int: pl.Int64,
            str: pl.Utf8,
            float: pl.Float64,
            bool: pl.Boolean,
            "int": pl.Int64,
            "str": pl.Utf8,
            "float": pl.Float64,
            "bool": pl.Boolean,
            "datetime": pl.Datetime,
            "date": pl.Date,
            "timestamp": pl.Datetime,
        }
        return mapping.get(dtype, dtype)

    def to_native(self, data: Any) -> Any:
        """Convert ``data`` to a Polars DataFrame."""
        if isinstance(data, ibis.Table):
            return data.to_polars()
        return data
