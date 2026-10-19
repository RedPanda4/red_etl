"""Ibis-native Pandera validator.

This validator uses ``pandera.ibis`` and works directly on Ibis ``Table``
expressions without converting them to a backend-native DataFrame first.
"""

from __future__ import annotations

from typing import Any

import ibis
import pandera.ibis as pa

from red_etl.validation.pandera.base import BasePanderaValidator


class IbisPanderaValidator(BasePanderaValidator):
    """Validate Ibis ``Table`` expressions using ``pandera.ibis``."""

    @property
    def pandera_module(self) -> Any:
        """Return ``pandera.ibis``."""
        return pa

    def map_dtype(self, dtype: type | str) -> Any:
        """Map a ``Column.dtype`` to an Ibis data type."""
        return ibis.dtype(dtype) if isinstance(dtype, type) else ibis.dtype(str(dtype))

    def to_native(self, data: Any) -> Any:
        """Return the Ibis table unchanged."""
        if not isinstance(data, ibis.Table):
            raise TypeError(
                f"IbisPanderaValidator expects an ibis.Table, got {type(data).__name__}"
            )
        return data
