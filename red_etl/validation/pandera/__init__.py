"""Pandera validators for ``RedMeta`` schemas.

This package provides backend-specific Pandera validators. The classes here
are registered as the package-default validators for their respective
backends; users can override or extend them via the generic
:func:`red_etl.validation.register_validator` registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

from red_etl.validation.base import register_validator
from red_etl.validation.pandera.base import BasePanderaValidator
from red_etl.validation.pandera.ibis_validator import IbisPanderaValidator
from red_etl.validation.pandera.pandas import PandasPanderaValidator
from red_etl.validation.pandera.polars import PolarsPanderaValidator

if TYPE_CHECKING:
    pass

__all__ = [
    "BasePanderaValidator",
    "IbisPanderaValidator",
    "PandasPanderaValidator",
    "PolarsPanderaValidator",
]

# Register Pandera validators as the package defaults for these backends.
register_validator("pandas", PandasPanderaValidator)
register_validator("polars", PolarsPanderaValidator)


def _guess_validator(data: Any) -> BasePanderaValidator:
    """Return a default Pandera validator based on the input data type.

    This is used by :func:`red_etl.validation.validate` when no backend is
    supplied. It always picks a Pandera validator; non-Pandera validators must
    be selected explicitly via ``backend=...`` or ``validator=...``.

    """
    if isinstance(data, ibis.Table):
        return IbisPanderaValidator()
    module = getattr(data, "__module__", "")
    if "polars" in module:
        return PolarsPanderaValidator()
    return PandasPanderaValidator()
