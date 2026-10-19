"""PySpark-native Pandera validator (placeholder).

This module shows where a PySpark-native validator would live. It is not
registered by default because ``pandera.pyspark`` is an optional extra and the
mapping logic is not implemented yet.
"""

from __future__ import annotations

from typing import Any

from red_etl.validation.pandera.base import BasePanderaValidator


class SparkPanderaValidator(BasePanderaValidator):
    """Placeholder for a PySpark-native Pandera validator.

    Register it once ``pandera.pyspark`` support is implemented:

    >>> from red_etl.validation.pandera import register_validator
    >>> from red_etl.validation.pandera.spark import SparkPanderaValidator
    >>> register_validator("spark", SparkPanderaValidator)

    """

    @property
    def pandera_module(self) -> Any:
        """Return ``pandera.pyspark``.

        This placeholder raises immediately. A concrete implementation should
        ``import pandera.pyspark`` here and return it.
        """
        raise NotImplementedError(
            "Spark validation is not implemented yet. "
            "Install pandera[pyspark] and implement map_dtype/to_native "
            "in a subclass."
        )

    def map_dtype(self, dtype: type | str) -> Any:
        """Map a ``Column.dtype`` to a PySpark data type."""
        raise NotImplementedError("Spark dtype mapping is not implemented yet.")

    def to_native(self, data: Any) -> Any:
        """Convert ``data`` to a PySpark DataFrame."""
        raise NotImplementedError("Spark native conversion is not implemented yet.")
