"""CSV sources and sinks for red-etl.

This module is only available when ``pandas`` is installed. Polars support
is optional and is used when ``polars`` is installed.

Sources return an Ibis ``Table`` expression. Sinks accept an Ibis ``Table``
expression and delegate the actual writing to the supplied backend.

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
        "CSV I/O requires pandas. Install it with: pip install 'red-etl[pandas]'"
    ) from exc

from red_etl.backends.base import Backend


class CSVSource(Source):
    """Read a CSV file into an Ibis ``Table`` expression.

    The actual reading is delegated to the supplied backend so that the
    resulting table is backed by the engine you intend to use (Pandas,
    Polars, etc.).

    Parameters
    ----------
    path
        Path or URL to the CSV file.
    separator
        Field delimiter. Default is comma.
    encoding
        File encoding. Default is ``"utf-8"``.
    header
        Whether the file has a header row. If ``False``, columns are named
        with integers.

    Examples
    --------
    >>> from red_etl.io.csv import CSVSource
    >>> from red_etl.backends.pandas import PandasBackend
    >>> source = CSVSource("data.csv", separator=";", encoding="latin1")
    >>> table = source.read(PandasBackend())

    """

    def __init__(
        self,
        path: str | Path,
        *,
        separator: str = ",",
        encoding: str = "utf-8",
        header: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize a CSV source.

        Parameters
        ----------
        path
            Path or URL to the CSV file.
        separator
            Field delimiter.
        encoding
            File encoding.
        header
            Whether the file has a header row.
        **kwargs
            Additional reader-specific options forwarded to the backend.
        """
        self.path = str(path)
        self.separator = separator
        self.encoding = encoding
        self.header = header
        self.kwargs = kwargs

    def read(self, backend: Backend) -> ibis.Table:
        """Read the CSV file and return an Ibis ``Table`` expression.

        Parameters
        ----------
        backend
            Backend used to read the file and back the resulting table.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the CSV data.
        """
        from red_etl.backends.pandas import PandasBackend
        from red_etl.backends.polars import PolarsBackend

        if isinstance(backend, PandasBackend):
            return backend.read_csv(
                self.path,
                separator=self.separator,
                encoding=self.encoding,
                header=self.header,
                **self.kwargs,
            )
        if isinstance(backend, PolarsBackend):
            return backend.read_csv(
                self.path,
                separator=self.separator,
                encoding=self.encoding,
                header=self.header,
                **self.kwargs,
            )
        raise NotImplementedError(
            f"CSVSource does not support backend '{getattr(backend, 'name', type(backend).__name__)}'"
        )


class CSVSink(Sink):
    """Write an Ibis ``Table`` expression to a CSV file.

    The actual writing is delegated to the supplied backend so that the
    table is materialized using the engine that produced it.

    Parameters
    ----------
    path
        Path or URL for the output CSV file.
    separator
        Field delimiter. Default is comma.
    encoding
        File encoding. Default is ``"utf-8"``.
    header
        Whether to write the column names.
    index
        Whether to write the row index. Pandas only.

    Examples
    --------
    >>> from red_etl.io.csv import CSVSink
    >>> from red_etl.backends.pandas import PandasBackend
    >>> sink = CSVSink("output.csv", separator=";")
    >>> sink.write(table, PandasBackend())

    """

    def __init__(
        self,
        path: str | Path,
        *,
        separator: str = ",",
        encoding: str = "utf-8",
        header: bool = True,
        index: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a CSV sink.

        Parameters
        ----------
        path
            Path or URL for the output file.
        separator
            Field delimiter.
        encoding
            File encoding.
        header
            Whether to write the column header.
        index
            Whether to write the row index (Pandas only).
        **kwargs
            Additional writer-specific options forwarded to the backend.
        """
        self.path = str(path)
        self.separator = separator
        self.encoding = encoding
        self.header = header
        self.index = index
        self.kwargs = kwargs

    def write(self, table: ibis.Table, backend: Backend) -> None:
        """Write ``table`` to CSV using the supplied backend.

        Parameters
        ----------
        table
            Ibis table expression to write.
        backend
            Backend used to materialize and write the table.
        """
        from red_etl.backends.pandas import PandasBackend
        from red_etl.backends.polars import PolarsBackend

        if isinstance(backend, PandasBackend):
            backend.write_csv(
                table,
                self.path,
                separator=self.separator,
                encoding=self.encoding,
                header=self.header,
                index=self.index,
                **self.kwargs,
            )
            return
        if isinstance(backend, PolarsBackend):
            backend.write_csv(
                table,
                self.path,
                separator=self.separator,
                header=self.header,
                **self.kwargs,
            )
            return
        raise NotImplementedError(
            f"CSVSink does not support backend '{getattr(backend, 'name', type(backend).__name__)}'"
        )
