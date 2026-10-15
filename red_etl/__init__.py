"""Red ETL — a metadata-first, backend-agnostic data cleaning framework.

This package provides a small core for declaring table schemas as Python
classes (``RedMeta``) and applying backend-specific transformations to
DataFrames. Backends such as Pandas, Polars or PySpark are optional and
live in separate submodules under :mod:`red_etl.backends`.
"""

from red_etl.column import Column
from red_etl.meta import RedMeta
from red_etl.pipeline import apply_transforms
from red_etl.transforms import (
    ConcatColumns,
    ExplodeDict,
    ExplodeList,
    OutputField,
    RegexExtract,
    ToBool,
    ToDate,
    ToDateTime,
    ToNumeric,
    Transform,
)

__all__ = [
    "Column",
    "ConcatColumns",
    "ExplodeDict",
    "ExplodeList",
    "OutputField",
    "RedMeta",
    "RegexExtract",
    "ToBool",
    "ToDate",
    "ToDateTime",
    "ToNumeric",
    "Transform",
    "apply_transforms",
]
