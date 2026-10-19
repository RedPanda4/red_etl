"""Optional validation adapters for red-etl.

This package provides validators that check whether a dataset matches a
``RedMeta`` schema. Each submodule is optional and may require additional
dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from red_etl.validation.base import (
    Validator,
    get_validator,
    list_registered_backends,
    register_validator,
    validate_schema,
)

# Importing the Pandera package registers its validators as defaults.
from red_etl.validation.pandera import (
    BasePanderaValidator,
    IbisPanderaValidator,
    PandasPanderaValidator,
    PolarsPanderaValidator,
)
from red_etl.validation.pandera import _guess_validator

if TYPE_CHECKING:
    from red_etl.backends.base import Backend

__all__ = [
    "BasePanderaValidator",
    "IbisPanderaValidator",
    "PandasPanderaValidator",
    "PolarsPanderaValidator",
    "Validator",
    "get_validator",
    "list_registered_backends",
    "register_validator",
    "validate",
    "validate_schema",
]


def validate(
    data: object,
    schema: type,
    *,
    backend: Backend | None = None,
    validator: Validator | None = None,
) -> object:
    """Validate ``data`` against a ``RedMeta`` schema.

    This helper builds the validation schema from the ``RedMeta`` class and
    runs it against the supplied data. By default it uses a validator chosen
    from the backend registry or inferred from the data type.

    Parameters
    ----------
    data
        An Ibis ``Table`` expression or a native dataset.
    schema
        A ``RedMeta`` subclass describing the expected columns and types.
    backend
        Optional backend used to select a backend-aware validator. This avoids
        converting large datasets to Pandas just for validation.
    validator
        An optional validator instance. If omitted, a backend-aware validator
        is created.

    Returns
    -------
    object
        The validated result in the format expected by the chosen validator.

    Examples
    --------
    >>> from red_etl import RedMeta, Column
    >>> from red_etl.validation import validate
    >>> class User(RedMeta):
    ...     id = Column(int)
    ...     name = Column(str)
    >>> validate(df, User)  # doctest: +SKIP

    """
    if validator is None:
        validator = get_validator(backend) if backend is not None else _guess_validator(data)
    validator.from_schema(schema)
    return validator.validate(data)
