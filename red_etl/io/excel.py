"""Excel sources and sinks for red-etl.

This module is only available when ``pandas`` and ``openpyxl`` are
installed.

Sources return an Ibis ``Table`` expression. Sinks accept an Ibis ``Table``
expression and delegate writing to Pandas (Excel is not natively supported
by Ibis backends).

"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ibis

from red_etl.io.base import Sink, Source

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Excel I/O requires pandas. Install it with: pip install 'red-etl[pandas]'"
    ) from exc

from red_etl.backends.base import Backend
from red_etl.backends.pandas import PandasBackend


class ExcelSource(Source):
    """Read an Excel file into an Ibis ``Table`` expression.

    Excel is read through Pandas and then converted to an Ibis table.

    Parameters
    ----------
    path
        Path or URL to the Excel file.
    sheet_name
        Sheet to read. Can be a string sheet name, an integer index, or a
        list of sheet names/indexes. Default is the first sheet.
    header
        Row to use as column names. Default is ``0`` (first row).

    Examples
    --------
    >>> from red_etl.io.excel import ExcelSource
    >>> from red_etl.backends.pandas import PandasBackend
    >>> source = ExcelSource("data.xlsx", sheet_name="Users", header=0)
    >>> table = source.read(PandasBackend())

    """

    def __init__(
        self,
        path: str | Path,
        *,
        sheet_name: str | int | list[str | int] | None = 0,
        header: int = 0,
        **kwargs: Any,
    ) -> None:
        """Initialize an Excel source.

        Parameters
        ----------
        path
            Path or URL to the Excel file.
        sheet_name
            Sheet name, index, or list of names/indexes.
        header
            Row to use as column header.
        **kwargs
            Additional options forwarded to ``pandas.read_excel``.
        """
        self.path = str(path)
        self.sheet_name = sheet_name
        self.header = header
        self.kwargs = kwargs

    def read(self, backend: Backend) -> ibis.Table:
        """Read the Excel file and return an Ibis ``Table`` expression.

        Parameters
        ----------
        backend
            Backend used to back the resulting table. Currently only
            ``PandasBackend`` is supported.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the Excel data.
        """
        if not isinstance(backend, PandasBackend):
            raise NotImplementedError(
                "ExcelSource currently only supports PandasBackend"
            )
        df = pd.read_excel(
            self.path,
            sheet_name=self.sheet_name,
            header=self.header,
            **self.kwargs,
        )
        return ibis.memtable(df)


class ExcelSink(Sink):
    """Write an Ibis ``Table`` expression to an Excel file.

    The table is materialized through Pandas and then written to Excel.

    Parameters
    ----------
    path
        Path or URL for the output Excel file.
    sheet_name
        Target sheet name. Default is ``"Sheet1"``.
    index
        Whether to write the row index.

    Examples
    --------
    >>> from red_etl.io.excel import ExcelSink
    >>> from red_etl.backends.pandas import PandasBackend
    >>> sink = ExcelSink("output.xlsx", sheet_name="Users")
    >>> sink.write(table, PandasBackend())

    """

    def __init__(
        self,
        path: str | Path,
        *,
        sheet_name: str = "Sheet1",
        index: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize an Excel sink.

        Parameters
        ----------
        path
            Path or URL for the output file.
        sheet_name
            Target sheet name.
        index
            Whether to write the row index.
        **kwargs
            Additional options forwarded to ``DataFrame.to_excel``.
        """
        self.path = str(path)
        self.sheet_name = sheet_name
        self.index = index
        self.kwargs = kwargs

    def write(self, table: ibis.Table, backend: Backend) -> None:
        """Write ``table`` to Excel using Pandas.

        Parameters
        ----------
        table
            Ibis table expression to write.
        backend
            Backend used to materialize the table. Currently only
            ``PandasBackend`` is supported.
        """
        if not isinstance(backend, PandasBackend):
            raise NotImplementedError(
                "ExcelSink currently only supports PandasBackend"
            )
        df = backend.from_ibis_table(table)
        df.to_excel(
            self.path,
            sheet_name=self.sheet_name,
            index=self.index,
            **self.kwargs,
        )
