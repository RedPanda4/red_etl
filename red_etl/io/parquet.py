"""Parquet sources and sinks for red-etl.

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
        "Parquet I/O requires pandas. Install it with: pip install 'red-etl[pandas]'"
    ) from exc

from red_etl.backends.base import Backend


class ParquetSource(Source):
    """Read a Parquet file into an Ibis ``Table`` expression.

    The actual reading is delegated to the supplied backend so that the
    resulting table is backed by the engine you intend to use.

    Parameters
    ----------
    path
        Path or URL to the Parquet file.
    columns
        Optional list of columns to read.

    Examples
    --------
    >>> from red_etl.io.parquet import ParquetSource
    >>> from red_etl.backends.pandas import PandasBackend
    >>> source = ParquetSource("data.parquet")
    >>> table = source.read(PandasBackend())

    """

    def __init__(
        self,
        path: str | Path,
        *,
        columns: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a Parquet source.

        Parameters
        ----------
        path
            Path or URL to the Parquet file.
        columns
            Optional subset of columns to read.
        **kwargs
            Additional reader-specific options forwarded to the backend.
        """
        self.path = str(path)
        self.columns = columns
        self.kwargs = kwargs

    def read(self, backend: Backend) -> ibis.Table:
        """Read the Parquet file and return an Ibis ``Table`` expression.

        Parameters
        ----------
        backend
            Backend used to read the file and back the resulting table.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the Parquet data.
        """
        from red_etl.backends.pandas import PandasBackend
        from red_etl.backends.polars import PolarsBackend

        if isinstance(backend, (PandasBackend, PolarsBackend)):
            return backend.read_parquet(
                self.path,
                columns=self.columns,
                **self.kwargs,
            )
        raise NotImplementedError(
            f"ParquetSource does not support backend '{getattr(backend, 'name', type(backend).__name__)}'"
        )


class ParquetSink(Sink):
    """Write an Ibis ``Table`` expression to a Parquet file.

    The actual writing is delegated to the supplied backend so that the
    table is materialized using the engine that produced it.

    Parameters
    ----------
    path
        Path or URL for the output Parquet file.
    compression
        Compression codec. Default is ``"snappy"``.
    index
        Whether to write the Pandas index. Pandas only.

    Examples
    --------
    >>> from red_etl.io.parquet import ParquetSink
    >>> from red_etl.backends.pandas import PandasBackend
    >>> sink = ParquetSink("output.parquet", compression="zstd")
    >>> sink.write(table, PandasBackend())

    """

    def __init__(
        self,
        path: str | Path,
        *,
        compression: str = "snappy",
        index: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a Parquet sink.

        Parameters
        ----------
        path
            Path or URL for the output file.
        compression
            Compression codec.
        index
            Whether to write the row index (Pandas only).
        **kwargs
            Additional writer-specific options forwarded to the backend.
        """
        self.path = str(path)
        self.compression = compression
        self.index = index
        self.kwargs = kwargs

    def write(self, table: ibis.Table, backend: Backend) -> None:
        """Write ``table`` to Parquet using the supplied backend.

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
            backend.write_parquet(
                table,
                self.path,
                compression=self.compression,
                index=self.index,
                **self.kwargs,
            )
            return
        if isinstance(backend, PolarsBackend):
            backend.write_parquet(
                table,
                self.path,
                compression=self.compression,
                **self.kwargs,
            )
            return
        raise NotImplementedError(
            f"ParquetSink does not support backend '{getattr(backend, 'name', type(backend).__name__)}'"
        )
