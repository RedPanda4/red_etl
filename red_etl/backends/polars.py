"""Polars backend for red-etl.

This backend is only available when ``polars`` is installed. It uses the
``ibis.polars`` backend to execute Ibis expressions directly against Polars
DataFrames and returns the result as a Polars DataFrame.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    import polars as pl

try:
    import polars as pl
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PolarsBackend requires polars. "
        "Install it with: pip install 'red-etl[polars]'"
    ) from exc

from red_etl.backends.base import Backend


def _polars_explode_list(transform, data: "pl.DataFrame") -> "pl.DataFrame":
    """Extract list elements into columns with strict length checking."""
    import polars as pl

    source = transform.input_columns()[0]
    outputs = transform.outputs
    expected = len(outputs)

    lengths = data.select(pl.col(source).list.len()).to_series()
    if lengths.drop_nulls().ne(expected).any():
        raise ValueError(
            f"Expected list of length {expected} in column {source!r}"
        )

    return data.with_columns(
        [
            pl.col(source).list.get(i).alias(field.name)
            for i, field in enumerate(outputs)
        ]
    )


def _polars_explode_dict(transform, data: "pl.DataFrame") -> "pl.DataFrame":
    """Extract dictionary values into columns."""
    import polars as pl

    source = transform.input_columns()[0]
    outputs = transform.outputs
    on_missing = transform.on_missing

    exprs = []
    for field in outputs:
        key = field.source_key if field.source_key is not None else field.name
        output = field.name
        if on_missing == "raise":
            expr = pl.col(source).struct.field(key).alias(output)
        else:
            expr = pl.col(source).struct.field(key).alias(output)
        exprs.append(expr)

    # For JSON strings, parse first
    # This is a simplified version assuming dict/struct values
    return data.with_columns(exprs)


def _polars_to_numeric(transform, data: "pl.DataFrame") -> "pl.DataFrame":
    """Cast a column to numeric with optional coercion of invalid values."""
    import polars as pl

    source = transform.input_columns()[0]
    output = transform.output_column
    dtype = transform.dtype
    errors = transform.errors

    strict = errors != "coerce"

    dtype_map = {
        "int64": pl.Int64,
        "float64": pl.Float64,
        "int32": pl.Int32,
        "float32": pl.Float32,
    }
    target = dtype_map.get(dtype, dtype)

    return data.with_columns(pl.col(source).cast(target, strict=strict).alias(output))


class PolarsBackend(Backend):
    """Backend that executes transformations using Ibis on Polars DataFrames.

    This backend uses the ``ibis.polars`` connection so that Ibis expressions
    are compiled to Polars operations. Results are returned as Polars
    DataFrames.

    """

    name = "polars"

    def __init__(self) -> None:
        """Initialize the Polars backend and its Ibis connection."""
        super().__init__()
        self._connection = ibis.polars.connect()
        self._table_counter = 0
        from red_etl.transforms import (
            ToNumeric,
            _ExplodeDictTransform,
            _ExplodeListTransform,
        )

        self.native_overrides[_ExplodeListTransform] = _polars_explode_list
        self.native_overrides[_ExplodeDictTransform] = _polars_explode_dict
        self.native_overrides[ToNumeric] = _polars_to_numeric

    def to_ibis_table(self, data: pl.DataFrame) -> ibis.Table:
        """Convert a Polars DataFrame into an Ibis table expression.

        Parameters
        ----------
        data
            A Polars DataFrame.

        Returns
        -------
        ibis.Table
            An Ibis table expression backed by ``data``.
        """
        self._table_counter += 1
        name = f"__red_etl_input_{self._table_counter}__"
        return self._connection.create_table(name, data)

    def from_ibis_table(self, table: ibis.Table) -> pl.DataFrame:
        """Execute an Ibis expression and return a Polars DataFrame.

        Parameters
        ----------
        table
            Ibis table expression to execute.

        Returns
        -------
        pl.DataFrame
            The executed result as a Polars DataFrame.
        """
        return table.to_polars()

    def read_csv(
        self,
        path: str,
        *,
        separator: str = ",",
        encoding: str = "utf-8",
        header: bool = True,
        **kwargs: Any,
    ) -> ibis.Table:
        """Read a CSV file via Polars into an Ibis table expression.

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
            Additional options passed to ``polars.read_csv``.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the CSV data.
        """
        df = pl.read_csv(
            path,
            separator=separator,
            encoding=encoding,
            has_header=header,
            **kwargs,
        )
        return self._connection.create_table("__red_etl_csv__", df)

    def write_csv(
        self,
        table: ibis.Table,
        path: str,
        *,
        separator: str = ",",
        header: bool = True,
        **kwargs: Any,
    ) -> None:
        """Write an Ibis table expression to CSV via Polars.

        Parameters
        ----------
        table
            Ibis table expression to write.
        path
            Path or URL for the output file.
        separator
            Field delimiter.
        header
            Whether to write the header row.
        **kwargs
            Additional options passed to ``DataFrame.write_csv``.
        """
        df = self.from_ibis_table(table)
        df.write_csv(path, separator=separator, include_header=header, **kwargs)

    def read_parquet(
        self,
        path: str,
        *,
        columns: list[str] | None = None,
        **kwargs: Any,
    ) -> ibis.Table:
        """Read a Parquet file via Polars into an Ibis table expression.

        Parameters
        ----------
        path
            Path or URL to the Parquet file.
        columns
            Optional subset of columns to read.
        **kwargs
            Additional options passed to ``polars.read_parquet``.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the Parquet data.
        """
        df = pl.read_parquet(path, columns=columns, **kwargs)
        return self._connection.create_table("__red_etl_parquet__", df)

    def write_parquet(
        self,
        table: ibis.Table,
        path: str,
        *,
        compression: str = "snappy",
        **kwargs: Any,
    ) -> None:
        """Write an Ibis table expression to Parquet via Polars.

        Parameters
        ----------
        table
            Ibis table expression to write.
        path
            Path or URL for the output file.
        compression
            Compression codec.
        **kwargs
            Additional options passed to ``DataFrame.write_parquet``.
        """
        df = self.from_ibis_table(table)
        df.write_parquet(path, compression=compression, **kwargs)
