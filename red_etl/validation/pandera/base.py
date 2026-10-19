"""Generic base class for Pandera-backed validators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import ibis

try:
    import pandera
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Pandera validators require pandera. "
        "Install it with: pip install 'red-etl[validation]'"
    ) from exc

from red_etl.meta import RedMeta
from red_etl.validation.base import Validator


class BasePanderaValidator(Validator, ABC):
    """Base class for a backend-specific Pandera validator.

    Subclasses provide three things: the Pandera module to use, a dtype mapper
    from ``Column.dtype`` to that module's types, and a converter from an
    Ibis table or native dataset to the format the module expects.

    This design avoids ``if backend == "polars"`` chains and lets new backends
    be added by creating a new subclass without touching existing code.

    """

    def __init__(self) -> None:
        """Initialize the validator with an empty schema."""
        self._schema: Any | None = None

    def from_schema(self, schema: type[RedMeta]) -> Any:
        """Build a Pandera schema from a ``RedMeta`` class.

        Parameters
        ----------
        schema
            A ``RedMeta`` subclass describing the expected columns and types.

        Returns
        -------
        Any
            The backend-specific Pandera schema object.
        """
        pm = self.pandera_module
        columns: dict[str, Any] = {}
        for name, column in schema.columns().items():
            dtype = self.map_dtype(column.dtype)
            columns[name] = pm.Column(dtype, nullable=column.nullable)

        self._schema = pm.DataFrameSchema(columns, strict=True)
        return self._schema

    def validate(self, data: Any) -> Any:
        """Validate ``data`` against the previously built schema.

        Parameters
        ----------
        data
            An Ibis ``Table`` expression or a native dataset.

        Returns
        -------
        Any
            The validated result in the format expected by the chosen Pandera
            module.

        Raises
        ------
        RuntimeError
            If :meth:`from_schema` has not been called first.
        """
        if self._schema is None:
            raise RuntimeError("from_schema must be called before validate")
        return self._schema.validate(self.to_native(data))

    @property
    @abstractmethod
    def pandera_module(self) -> Any:
        """Return the Pandera submodule used by this validator."""

    @abstractmethod
    def map_dtype(self, dtype: type | str) -> Any:
        """Map a ``Column.dtype`` to a type accepted by :attr:`pandera_module`."""

    @abstractmethod
    def to_native(self, data: Any) -> Any:
        """Convert ``data`` to the format expected by :attr:`pandera_module`."""


def _to_pandas_fallback(data: Any) -> Any:
    """Materialize an Ibis table or Polars DataFrame to Pandas.

    This is a fallback for validators that operate on Pandas-native Pandera.
    """
    if isinstance(data, ibis.Table):
        return data.execute()
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    return data
