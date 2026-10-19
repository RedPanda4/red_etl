"""Abstract base class, lightweight schema checks and validator registry.

Validation is an optional concern. Concrete validators live in submodules and
are imported only when needed, so the core ``red_etl`` package does not depend
on any validation library.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

import ibis

from red_etl.meta import RedMeta

if TYPE_CHECKING:
    from red_etl.backends.base import Backend


class Validator(ABC):
    """Abstract base class for a schema validator.

    A validator turns a ``RedMeta`` schema into a backend-specific validation
    object and can validate an Ibis table or native dataset against it.

    Concrete subclasses are responsible for importing their optional
    dependency and failing gracefully when it is missing.

    """

    @abstractmethod
    def from_schema(self, schema: type[RedMeta]) -> Any:
        """Build the validator from a ``RedMeta`` schema.

        Parameters
        ----------
        schema
            A ``RedMeta`` subclass describing the expected columns and types.

        Returns
        -------
        Any
            The backend-specific validation object. The exact type depends on
            the concrete validator.
        """

    @abstractmethod
    def validate(self, data: Any) -> Any:
        """Validate ``data`` against the schema built by :meth:`from_schema`.

        Parameters
        ----------
        data
            An Ibis ``Table`` expression or a native dataset (for example a
            Pandas or Polars DataFrame).

        Returns
        -------
        Any
            The validated result in the format expected by the validator.

        Raises
        ------
        RuntimeError
            If :meth:`from_schema` has not been called first.
        """


def validate_schema(table: ibis.Table, schema: type[RedMeta]) -> None:
    """Validate that an Ibis table schema matches a ``RedMeta`` schema.

    This check is lightweight: it compares column names and Ibis data types
    without executing the table or pulling any rows into memory. It is safe to
    use on large datasets regardless of the backing engine.

    Parameters
    ----------
    table
        An Ibis ``Table`` expression.
    schema
        A ``RedMeta`` subclass describing the expected columns and types.

    Raises
    ------
    ValueError
        If column names do not match exactly or if a column type does not
        match the schema.
    """
    expected_columns = schema.columns()
    expected_names = set(expected_columns)
    actual_names = set(table.columns)

    if expected_names != actual_names:
        missing = expected_names - actual_names
        extra = actual_names - expected_names
        parts: list[str] = []
        if missing:
            parts.append(f"missing columns: {sorted(missing)}")
        if extra:
            parts.append(f"extra columns: {sorted(extra)}")
        raise ValueError(f"Schema mismatch: {', '.join(parts)}")

    ibis_schema = table.schema()
    for name, column in expected_columns.items():
        expected_dtype = _redmeta_dtype_to_ibis(column.dtype)
        actual_dtype = ibis_schema[name]
        if expected_dtype != actual_dtype:
            raise ValueError(
                f"Column {name!r} expected type {expected_dtype}, got {actual_dtype}"
            )


def _redmeta_dtype_to_ibis(dtype: type | str) -> ibis.DataType:
    """Map a ``Column.dtype`` to an Ibis data type."""
    return ibis.dtype(dtype) if isinstance(dtype, type) else ibis.dtype(str(dtype))


# Generic validator registry. Concrete validator packages register defaults
# when they are imported; users can also register or override entries
# programmatically via register_validator().
T = TypeVar("T", bound="Validator")
_VALIDATOR_REGISTRY: dict[str, type[Validator]] = {}


def register_validator(backend_name: str, validator_cls: type[T]) -> type[T]:
    """Register a validator class for a backend.

    This registry is generic: it accepts any subclass of :class:`Validator`,
    not just Pandera-based validators.

    Parameters
    ----------
    backend_name
        The ``name`` of the backend that ``validator_cls`` can validate.
    validator_cls
        A concrete subclass of :class:`Validator`.

    Returns
    -------
    type[T]
        The registered class, so the call can be used as a decorator.

    Examples
    --------
    >>> from red_etl.validation import register_validator, Validator
    >>> @register_validator("my_backend")
    ... class MyValidator(Validator):
    ...     pass

    """
    if not issubclass(validator_cls, Validator):
        raise TypeError("validator_cls must subclass Validator")
    _VALIDATOR_REGISTRY[backend_name] = validator_cls
    return validator_cls


def get_validator(backend: Backend) -> Validator:
    """Return the validator registered for ``backend``.

    Parameters
    ----------
    backend
        A concrete :class:`Backend` instance.

    Returns
    -------
    Validator
        An instance of the registered validator class.

    Raises
    ------
    NotImplementedError
        If no validator is registered for the backend name.
    """
    name = getattr(backend, "name", "")
    cls = _VALIDATOR_REGISTRY.get(name)
    if cls is None:
        implemented = list(_VALIDATOR_REGISTRY.keys())
        raise NotImplementedError(
            f"Validation for backend {name!r} is not implemented. "
            f"Implemented backends: {implemented}. "
            f"Use validate_schema() for a lightweight schema check instead, "
            f"or register a validator with register_validator()."
        )
    return cls()


def list_registered_backends() -> list[str]:
    """Return the names of backends with a registered validator."""
    return list(_VALIDATOR_REGISTRY.keys())
