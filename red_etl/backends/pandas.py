"""Pandas backend for red-etl.

This backend is only available when ``pandas`` is installed. It converts
input ``pandas.DataFrame`` objects into Ibis table expressions using
``ibis.memtable``, executes Ibis expressions, and returns the result as a
Pandas DataFrame.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ibis

if TYPE_CHECKING:
    import pandas as pd

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PandasBackend requires pandas. "
        "Install it with: pip install 'red-etl[pandas]'"
    ) from exc

from red_etl.backends.base import Backend


def _pandas_explode_list(transform, data: pd.DataFrame) -> pd.DataFrame:
    """Extract list elements into columns with strict length checking."""
    source = transform.input_columns()[0]
    outputs = transform.outputs
    expected = len(outputs)

    for value in data[source]:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        if len(value) != expected:
            raise ValueError(
                f"Expected list of length {expected} in column {source!r}, got {len(value)}"
            )

    for i, field in enumerate(outputs):
        data[field.name] = data[source].apply(
            lambda x: x[i] if x is not None and not (isinstance(x, float) and pd.isna(x)) else None
        )
    return data


def _pandas_explode_dict(transform, data: pd.DataFrame) -> pd.DataFrame:
    """Extract dictionary values into columns."""
    source = transform.input_columns()[0]
    outputs = transform.outputs
    on_missing = transform.on_missing

    for field in outputs:
        key = field.source_key if field.source_key is not None else field.name
        output = field.name
        values = []
        for value in data[source]:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                values.append(None)
            elif isinstance(value, str):
                # Try to parse JSON string
                import json
                parsed = json.loads(value)
                if key not in parsed:
                    if on_missing == "raise":
                        raise KeyError(f"Key {key!r} not found in dictionary")
                    values.append(None)
                else:
                    values.append(parsed[key])
            elif isinstance(value, dict):
                if key not in value:
                    if on_missing == "raise":
                        raise KeyError(f"Key {key!r} not found in dictionary")
                    values.append(None)
                else:
                    values.append(value[key])
            else:
                raise TypeError(f"Unsupported value type for ExplodeDict: {type(value)}")
        data[output] = values
    return data


def _pandas_to_numeric(transform, data: pd.DataFrame) -> pd.DataFrame:
    """Cast a column to numeric with optional coercion of invalid values."""
    source = transform.input_columns()[0]
    output = transform.output_column
    dtype = transform.dtype
    errors = transform.errors

    pandas_errors = "coerce" if errors == "coerce" else "raise"
    data[output] = pd.to_numeric(data[source], errors=pandas_errors)

    # Map Ibis dtype names to numpy/pandas dtypes
    dtype_map = {
        "int64": "int64",
        "float64": "float64",
        "int32": "int32",
        "float32": "float32",
    }
    target = dtype_map.get(dtype, dtype)
    if target:
        data[output] = data[output].astype(target)
    return data


class PandasBackend(Backend):
    """Backend that executes transformations using Ibis and returns Pandas DataFrames.

    This backend uses ``ibis.memtable`` to expose Pandas DataFrames to Ibis.
    All transformations are executed as Ibis expressions unless the backend
    has a registered native override for a specific transform.

    """

    name = "pandas"

    def __init__(self) -> None:
        """Initialize the Pandas backend and register native overrides."""
        super().__init__()
        from red_etl.transforms import (
            ToNumeric,
            _ExplodeDictTransform,
            _ExplodeListTransform,
        )

        self.native_overrides[_ExplodeListTransform] = _pandas_explode_list
        self.native_overrides[_ExplodeDictTransform] = _pandas_explode_dict
        self.native_overrides[ToNumeric] = _pandas_to_numeric

    def to_ibis_table(self, data: pd.DataFrame) -> ibis.Table:
        """Convert a Pandas DataFrame into an Ibis table expression.

        Parameters
        ----------
        data
            A Pandas DataFrame.

        Returns
        -------
        ibis.Table
            An Ibis table expression backed by ``data``.
        """
        return ibis.memtable(data)

    def from_ibis_table(self, table: ibis.Table) -> pd.DataFrame:
        """Execute an Ibis expression and return a Pandas DataFrame.

        Parameters
        ----------
        table
            Ibis table expression to execute.

        Returns
        -------
        pd.DataFrame
            The executed result as a Pandas DataFrame.
        """
        return table.execute()

    def read_csv(
        self,
        path: str,
        *,
        separator: str = ",",
        encoding: str = "utf-8",
        header: bool = True,
        **kwargs: Any,
    ) -> ibis.Table:
        """Read a CSV file via Pandas into an Ibis table expression.

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
            Additional options passed to ``pandas.read_csv``.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the CSV data.
        """
        df = pd.read_csv(
            path,
            sep=separator,
            encoding=encoding,
            header=0 if header else None,
            **kwargs,
        )
        return ibis.memtable(df)

    def write_csv(
        self,
        table: ibis.Table,
        path: str,
        *,
        separator: str = ",",
        encoding: str = "utf-8",
        header: bool = True,
        index: bool = False,
        **kwargs: Any,
    ) -> None:
        """Write an Ibis table expression to CSV via Pandas.

        Parameters
        ----------
        table
            Ibis table expression to write.
        path
            Path or URL for the output file.
        separator
            Field delimiter.
        encoding
            File encoding.
        header
            Whether to write the header row.
        index
            Whether to write the row index.
        **kwargs
            Additional options passed to ``DataFrame.to_csv``.
        """
        df = self.from_ibis_table(table)
        df.to_csv(
            path,
            sep=separator,
            encoding=encoding,
            header=header,
            index=index,
            **kwargs,
        )

    def read_parquet(
        self,
        path: str,
        *,
        columns: list[str] | None = None,
        **kwargs: Any,
    ) -> ibis.Table:
        """Read a Parquet file via Pandas into an Ibis table expression.

        Parameters
        ----------
        path
            Path or URL to the Parquet file.
        columns
            Optional subset of columns to read.
        **kwargs
            Additional options passed to ``pandas.read_parquet``.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the Parquet data.
        """
        df = pd.read_parquet(path, columns=columns, **kwargs)
        return ibis.memtable(df)

    def write_parquet(
        self,
        table: ibis.Table,
        path: str,
        *,
        compression: str = "snappy",
        index: bool = False,
        **kwargs: Any,
    ) -> None:
        """Write an Ibis table expression to Parquet via Pandas.

        Parameters
        ----------
        table
            Ibis table expression to write.
        path
            Path or URL for the output file.
        compression
            Compression codec.
        index
            Whether to write the row index.
        **kwargs
            Additional options passed to ``DataFrame.to_parquet``.
        """
        df = self.from_ibis_table(table)
        df.to_parquet(path, compression=compression, index=index, **kwargs)

    def read_sql(
        self,
        connection: str,
        *,
        query: str | None = None,
        schema: str | None = None,
        table_name: str | None = None,
        **kwargs: Any,
    ) -> ibis.Table:
        """Read data from SQL via Pandas into an Ibis table expression.

        Parameters
        ----------
        connection
            SQLAlchemy engine or connection string.
        query
            Raw SQL query.
        schema
            Database schema name.
        table_name
            Table name.
        **kwargs
            Additional options passed to ``pandas.read_sql``.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the SQL data.
        """
        if query is None:
            if table_name is None:
                raise ValueError("SQL read requires either 'query' or 'table_name'.")
            full_name = f"{schema}.{table_name}" if schema else table_name
            query = f"SELECT * FROM {full_name}"
        df = pd.read_sql(query, connection, **kwargs)
        return ibis.memtable(df)

    def write_sql(
        self,
        table: ibis.Table,
        connection: str,
        table_name: str,
        *,
        schema: str | None = None,
        if_exists: str = "fail",
        **kwargs: Any,
    ) -> None:
        """Write an Ibis table expression to SQL via Pandas.

        Parameters
        ----------
        table
            Ibis table expression to write.
        connection
            SQLAlchemy engine or connection string.
        table_name
            Target table name.
        schema
            Optional database schema name.
        if_exists
            Behavior when the target table exists.
        **kwargs
            Additional options passed to ``DataFrame.to_sql``.
        """
        df = self.from_ibis_table(table)
        df.to_sql(
            table_name,
            connection,
            schema=schema,
            if_exists=if_exists,
            index=False,
            **kwargs,
        )
