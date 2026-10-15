"""Optional I/O adapters for red-etl.

This package provides sources and sinks for reading and writing data in
various formats and systems. Each submodule is optional and may require
additional dependencies.

"""

from red_etl.io.base import Sink, Source
from red_etl.io.csv import CSVSource, CSVSink
from red_etl.io.parquet import ParquetSource, ParquetSink
from red_etl.io.sql import SQLSource, SQLSink

__all__ = [
    "CSVSource",
    "CSVSink",
    "ParquetSource",
    "ParquetSink",
    "Sink",
    "Source",
    "SQLSource",
    "SQLSink",
]

# Excel I/O is optional even within the optional I/O package because it needs
# openpyxl. It is available via ``from red_etl.io.excel import ExcelSource``.
