"""Abstract base class for red-etl execution backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

import ibis

if TYPE_CHECKING:
    from red_etl.transforms import Transform


class Backend(ABC):
    """Abstract base class for a backend that executes transformations.

    A backend is responsible for three things:

    1. Converting native data (e.g. a ``pandas.DataFrame``) into an Ibis
       ``Table`` expression.
    2. Applying transformations. By default every transform is converted to
       an Ibis expression and executed as a single batch, but a backend may
       register *native overrides* for operations where Ibis support is weak
       or buggy.
    3. Converting the resulting Ibis ``Table`` back into the native data
       format.

    Subclasses must implement :meth:`to_ibis_table` and
    :meth:`from_ibis_table`. They may optionally populate
    :attr:`native_overrides` with backend-specific implementations.

    """

    name: str = ""

    def __init__(self) -> None:
        """Initialize the backend and its native override registry."""
        self.native_overrides: dict[type[Transform], Callable[[Transform, Any], Any]] = {}

    def supports_native(self, transform: Transform) -> bool:
        """Check whether this backend has a native override for ``transform``.

        Parameters
        ----------
        transform
            The transformation to check.

        Returns
        -------
        bool
            ``True`` if a native override is registered, otherwise ``False``.
        """
        return type(transform) in self.native_overrides

    def apply_native(self, transform: Transform, data: Any) -> Any:
        """Apply the native override for ``transform`` to ``data``.

        Parameters
        ----------
        transform
            The transformation to apply.
        data
            The dataset in the backend's native format.

        Returns
        -------
        Any
            The transformed dataset in the backend's native format.

        Raises
        ------
        KeyError
            If no native override exists for the transform type.
        """
        impl = self.native_overrides[type(transform)]
        return impl(transform, data)

    @abstractmethod
    def to_ibis_table(self, data: Any) -> ibis.Table:
        """Convert native data into an Ibis ``Table`` expression.

        Parameters
        ----------
        data
            Dataset in the backend's native format.

        Returns
        -------
        ibis.Table
            An Ibis table expression backed by ``data``.
        """

    @abstractmethod
    def from_ibis_table(self, table: ibis.Table) -> Any:
        """Execute an Ibis ``Table`` expression and return native data.

        Parameters
        ----------
        table
            Ibis table expression to execute.

        Returns
        -------
        Any
            The result in the backend's native format.
        """

    def execute_ibis(self, table: ibis.Table) -> Any:
        """Execute an Ibis table expression and materialize the result.

        The default implementation delegates to :meth:`from_ibis_table`.
        Backends may override this method to keep execution lazy.

        Parameters
        ----------
        table
            Ibis table expression to execute.

        Returns
        -------
        Any
            The result in the backend's native format.
        """
        return self.from_ibis_table(table)

    def read_csv(self, path: str, *, separator: str = ",", encoding: str = "utf-8", header: bool = True, **kwargs: Any) -> ibis.Table:
        """Read a CSV file into an Ibis table expression.

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
            Additional reader-specific options.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the CSV data.
        """
        raise NotImplementedError

    def write_csv(self, table: ibis.Table, path: str, *, separator: str = ",", encoding: str = "utf-8", header: bool = True, **kwargs: Any) -> None:
        """Write an Ibis table expression to a CSV file.

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
        **kwargs
            Additional writer-specific options.
        """
        raise NotImplementedError

    def read_parquet(self, path: str, *, columns: list[str] | None = None, **kwargs: Any) -> ibis.Table:
        """Read a Parquet file into an Ibis table expression.

        Parameters
        ----------
        path
            Path or URL to the Parquet file.
        columns
            Optional subset of columns to read.
        **kwargs
            Additional reader-specific options.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the Parquet data.
        """
        raise NotImplementedError

    def write_parquet(self, table: ibis.Table, path: str, *, compression: str = "snappy", **kwargs: Any) -> None:
        """Write an Ibis table expression to a Parquet file.

        Parameters
        ----------
        table
            Ibis table expression to write.
        path
            Path or URL for the output file.
        compression
            Compression codec.
        **kwargs
            Additional writer-specific options.
        """
        raise NotImplementedError

    def read_sql(self, connection: str, *, query: str | None = None, schema: str | None = None, table_name: str | None = None, **kwargs: Any) -> ibis.Table:
        """Read data from a SQL database into an Ibis table expression.

        Parameters
        ----------
        connection
            Connection string or engine.
        query
            Raw SQL query.
        schema
            Database schema name.
        table_name
            Table name.
        **kwargs
            Additional reader-specific options.

        Returns
        -------
        ibis.Table
            Ibis table expression backed by the SQL data.
        """
        raise NotImplementedError

    def write_sql(self, table: ibis.Table, connection: str, table_name: str, *, schema: str | None = None, if_exists: str = "fail", **kwargs: Any) -> None:
        """Write an Ibis table expression to a SQL database table.

        Parameters
        ----------
        table
            Ibis table expression to write.
        connection
            Connection string or engine.
        table_name
            Target table name.
        schema
            Optional database schema name.
        if_exists
            Behavior when the table exists: ``"fail"``, ``"replace"`` or
            ``"append"``.
        **kwargs
            Additional writer-specific options.
        """
        raise NotImplementedError
