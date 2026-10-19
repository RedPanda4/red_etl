"""Pandas-native Pandera validator."""

from __future__ import annotations

from typing import Any

import pandera.pandas as pa

from red_etl.validation.pandera.base import BasePanderaValidator, _to_pandas_fallback


class PandasPanderaValidator(BasePanderaValidator):
    """Validate Pandas DataFrames using ``pandera.pandas``."""

    @property
    def pandera_module(self) -> Any:
        """Return ``pandera.pandas``."""
        return pa

    def map_dtype(self, dtype: type | str) -> Any:
        """Map a ``Column.dtype`` to a ``pandera.pandas`` type."""
        mapping: dict[type | str, Any] = {
            int: pa.Int,
            str: pa.String,
            float: pa.Float,
            bool: pa.Bool,
            "int": pa.Int,
            "str": pa.String,
            "float": pa.Float,
            "bool": pa.Bool,
            "datetime": pa.DateTime,
            "date": pa.Date,
            "timestamp": pa.DateTime,
        }
        return mapping.get(dtype, dtype)

    def to_native(self, data: Any) -> Any:
        """Convert ``data`` to a Pandas DataFrame."""
        return _to_pandas_fallback(data)
