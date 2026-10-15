"""Backend adapters that execute ``RedMeta`` transformations on concrete engines.

Each submodule provides a backend for a specific engine. The backends are
optional: importing a submodule fails gracefully with an informative error
if its underlying engine dependency is not installed.

"""

from red_etl.backends.base import Backend
from red_etl.backends.pandas import PandasBackend
from red_etl.backends.polars import PolarsBackend

__all__ = ["Backend", "PandasBackend", "PolarsBackend"]
