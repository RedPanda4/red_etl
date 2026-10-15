"""SQL sources and sinks for red-etl.

This module is only available when ``pandas`` and ``sqlalchemy`` are
installed.

Sources return an Ibis ``Table`` expression. Sinks accept an Ibis ``Table``
expression and delegate writing to the supplied backend.

"""

from __future__ import annotations

from typing import Any

import ibis

from red_etl.io.base import Sink, Source

try:
    import pandas as pd
    import sqlalchemy as sa
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "SQL I/O requires pandas and sqlalchemy. "
        "Install them with: pip install 'red-etl[pandas]' sqlalchemy"
    ) from exc

from red_etl.backends.base import Backend


class SQLSource(Source):
    """Read data from a SQL database into an Ibis ``Table`` expression.

    The actual reading is delegated to the supplied backend.

    Parameters
    ----------
    connection
        SQLAlchemy engine or connection string.
    query
        Raw SQL query. If provided, ``schema`` and ``table_name`` are ignored.
    schema
        Database schema name. Used together with ``table_name``.
    table_name
        Table name to read. Used together with ``schema``.

    Examples
    --------
    >>> from red_etl.io.sql import SQLSource
    >>> from red_etl.backends.pandas import PandasBackend
    >>> source = SQLSource("sqlite:///data.db", table_name="users")
    >>> table = source.read(PandasBackend())

    """

    def __init__(
        self,
        connection: str | "sa.Engine",
        *,
        query: str | None = None,
        schema: str | None = None,
        table_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a SQL source.

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
            Additional reader-specific options forwarded to the backend.
        """
        self.connection = connection
        self.query = query
        self.schema = schema
        self.table_name = table_name
        self.kwargs = kwargs

    def read(self, backend: Backend) -> ibis.Table:
        """Read data from SQL and return an Ibis ``Table`` expression.

        Parameters
        ----------
        backend
            Backend used to read the data and back the resulting table.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the SQL data.
        """
        return backend.read_sql(
            self.connection,
            query=self.query,
            schema=self.schema,
            table_name=self.table_name,
            **self.kwargs,
        )


class SQLSink(Sink):
    """Write an Ibis ``Table`` expression to a SQL database table.

    The actual writing is delegated to the supplied backend.

    Parameters
    ----------
    connection
        SQLAlchemy engine or connection string.
    table_name
        Target table name.
    schema
        Optional database schema name.
    if_exists
        Behavior when the table already exists: ``"fail"``, ``"replace"`` or
        ``"append"``. Default is ``"fail"``.

    Examples
    --------
    >>> from red_etl.io.sql import SQLSink
    >>> from red_etl.backends.pandas import PandasBackend
    >>> sink = SQLSink("sqlite:///data.db", table_name="users_clean", if_exists="replace")
    >>> sink.write(table, PandasBackend())

    """

    def __init__(
        self,
        connection: str | "sa.Engine",
        table_name: str,
        *,
        schema: str | None = None,
        if_exists: str = "fail",
        **kwargs: Any,
    ) -> None:
        """Initialize a SQL sink.

        Parameters
        ----------
        connection
            SQLAlchemy engine or connection string.
        table_name
            Target table name.
        schema
            Optional database schema name.
        if_exists
            Behavior when the target table exists.
        **kwargs
            Additional writer-specific options forwarded to the backend.
        """
        self.connection = connection
        self.table_name = table_name
        self.schema = schema
        self.if_exists = if_exists
        self.kwargs = kwargs

    def write(self, table: ibis.Table, backend: Backend) -> None:
        """Write ``table`` to SQL using the supplied backend.

        Parameters
        ----------
        table
            Ibis table expression to write.
        backend
            Backend used to materialize and write the table.
        """
        backend.write_sql(
            table,
            self.connection,
            self.table_name,
            schema=self.schema,
            if_exists=self.if_exists,
            **self.kwargs,
        )
