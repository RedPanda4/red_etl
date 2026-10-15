"""Backend-agnostic transformation operations for ``RedMeta`` schemas."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import ibis

from red_etl.column import Column

if TYPE_CHECKING:
    pass


class Transform(ABC):
    """Abstract base class for a column-level transformation.

    A ``Transform`` describes how to derive or clean a single target column.
    By default each transform is converted to an Ibis expression via
    :meth:`to_ibis`. Backends may provide native overrides for operations
    where Ibis support is weak, but those overrides live in the backend, not
    in the transform.

    Subclasses must implement :meth:`to_ibis` and declare which columns they
    read from and which column they write to.

    """

    @property
    @abstractmethod
    def output_column(self) -> str:
        """Return the name of the column produced by this transformation."""

    def set_output_column(self, name: str) -> None:
        """Set the output column name when the transform is bound to a column.

        Parameters
        ----------
        name
            The name of the column that owns this transformation.
        """

    @abstractmethod
    def input_columns(self) -> list[str]:
        """Return the names of the columns this transformation reads from."""

    @abstractmethod
    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that applies this transformation.

        Parameters
        ----------
        table
            Ibis table expression representing the input data.

        Returns
        -------
        ibis.Table
            A new Ibis table expression with the transformation applied.
        """


class ConcatColumns(Transform):
    """Concatenate two or more string columns with a separator.

    Parameters
    ----------
    columns
        The columns to concatenate. These may be ``Column`` descriptors or
        plain strings. Using ``Column`` descriptors is preferred because it
        enables IDE autocompletion and avoids typos.
    separator
        The string placed between each column value.
    output
        The name of the resulting column. If omitted, the name is inferred
        from the attribute assignment on the ``RedMeta`` class.

    Examples
    --------
    >>> from red_etl import Column, RedMeta
    >>> from red_etl.transforms import ConcatColumns
    >>> class User(RedMeta):
    ...     first_name = Column(str)
    ...     last_name = Column(str)
    ...     full_name = Column(str, transform=ConcatColumns([first_name, last_name], separator=" "))

    """

    def __init__(
        self,
        columns: list[Column | str],
        *,
        separator: str = " ",
        output: str = "",
    ) -> None:
        """Initialize a ``ConcatColumns`` transformation.

        Parameters
        ----------
        columns
            Columns to concatenate.
        separator
            Separator placed between values.
        output
            Name of the output column.
        """
        if not columns:
            raise ValueError("ConcatColumns requires at least one column")
        self._columns = columns
        self.separator = separator
        self._output = output

    @property
    def output_column(self) -> str:
        """Return the name of the output column.

        Returns
        -------
        str
            The configured output column name. May be empty until the
            transform is bound to a ``Column`` descriptor.
        """
        return self._output

    def set_output_column(self, name: str) -> None:
        """Set the output column name from the owning column.

        Parameters
        ----------
        name
            The name of the column that owns this transformation.
        """
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        """Return the names of the columns being concatenated.

        Returns
        -------
        list[str]
            List of input column names.
        """
        return [_column_name(col) for col in self._columns]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that concatenates the input columns.

        Parameters
        ----------
        table
            Ibis table expression representing the input data.

        Returns
        -------
        ibis.Table
            A new table expression with the concatenated column.
        """
        names = self.input_columns()
        expr = table[names[0]]
        for name in names[1:]:
            expr = expr.concat(self.separator).concat(table[name])
        return table.mutate(**{self.output_column: expr})


class ToDate(Transform):
    """Parse a string column into a date column using a format string.

    Parameters
    ----------
    source_column
        The source string column. May be a ``Column`` descriptor or a string.
    format
        Date format string, e.g. ``"%Y-%m-%d"``.
    output
        Name of the resulting column. If omitted, inferred from the owning
        ``Column`` descriptor.

    Examples
    --------
    >>> class Event(RedMeta):
    ...     date_str = Column(str)
    ...     date = Column("date", transform=ToDate(date_str, "%Y-%m-%d"))

    """

    def __init__(
        self,
        source_column: Column | str,
        format: str,  # noqa: A002
        output: str = "",
    ) -> None:
        """Initialize a ``ToDate`` transformation.

        Parameters
        ----------
        source_column
            Source string column.
        format
            Date format string.
        output
            Name of the output column.
        """
        self.source_column = source_column
        self.format = format
        self._output = output

    @property
    def output_column(self) -> str:
        """Return the name of the output column."""
        return self._output

    def set_output_column(self, name: str) -> None:
        """Set the output column name from the owning column."""
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that parses the source string to a date.

        Parameters
        ----------
        table
            Ibis table expression.

        Returns
        -------
        ibis.Table
            Table expression with the parsed date column.
        """
        source = self.input_columns()[0]
        return table.mutate(**{self.output_column: table[source].as_date(self.format)})


class ToDateTime(Transform):
    """Parse a string column into a timestamp column using a format string.

    Parameters
    ----------
    source_column
        The source string column. May be a ``Column`` descriptor or a string.
    format
        Timestamp format string, e.g. ``"%Y-%m-%d %H:%M:%S"``.
    output
        Name of the resulting column. If omitted, inferred from the owning
        ``Column`` descriptor.

    Examples
    --------
    >>> class Event(RedMeta):
    ...     ts_str = Column(str)
    ...     ts = Column("datetime", transform=ToDateTime(ts_str, "%Y-%m-%d %H:%M:%S"))

    """

    def __init__(
        self,
        source_column: Column | str,
        format: str,  # noqa: A002
        output: str = "",
    ) -> None:
        """Initialize a ``ToDateTime`` transformation.

        Parameters
        ----------
        source_column
            Source string column.
        format
            Timestamp format string.
        output
            Name of the output column.
        """
        self.source_column = source_column
        self.format = format
        self._output = output

    @property
    def output_column(self) -> str:
        """Return the name of the output column."""
        return self._output

    def set_output_column(self, name: str) -> None:
        """Set the output column name from the owning column."""
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that parses the source string to a timestamp.

        Parameters
        ----------
        table
            Ibis table expression.

        Returns
        -------
        ibis.Table
            Table expression with the parsed timestamp column.
        """
        source = self.input_columns()[0]
        return table.mutate(
            **{self.output_column: table[source].as_timestamp(self.format)}
        )


class ToBool(Transform):
    """Convert a string or integer column to boolean.

    Values matching ``true_values`` become ``True``, values matching
    ``false_values`` become ``False``, and anything else becomes ``None``.

    Parameters
    ----------
    source_column
        The source column. May be a ``Column`` descriptor or a string.
    true_values
        Values that should map to ``True``. Defaults to ``["1", "true", "yes"]``.
    false_values
        Values that should map to ``False``. Defaults to ``["0", "false", "no"]``.
    output
        Name of the resulting column. If omitted, inferred from the owning
        ``Column`` descriptor.

    Examples
    --------
    >>> class User(RedMeta):
    ...     active_str = Column(str)
    ...     active = Column(bool, transform=ToBool(active_str, true_values=["1"], false_values=["0"]))

    """

    def __init__(
        self,
        source_column: Column | str,
        true_values: list[str] | None = None,
        false_values: list[str] | None = None,
        output: str = "",
    ) -> None:
        """Initialize a ``ToBool`` transformation.

        Parameters
        ----------
        source_column
            Source column.
        true_values
            Values mapped to ``True``.
        false_values
            Values mapped to ``False``.
        output
            Name of the output column.
        """
        self.source_column = source_column
        self.true_values = true_values if true_values is not None else ["1", "true", "yes"]
        self.false_values = false_values if false_values is not None else ["0", "false", "no"]
        self._output = output

    @property
    def output_column(self) -> str:
        """Return the name of the output column."""
        return self._output

    def set_output_column(self, name: str) -> None:
        """Set the output column name from the owning column."""
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that maps values to boolean.

        Parameters
        ----------
        table
            Ibis table expression.

        Returns
        -------
        ibis.Table
            Table expression with the boolean column.
        """
        source = table[self.input_columns()[0]]
        true_expr = source.isin(self.true_values)
        false_expr = source.isin(self.false_values)
        bool_expr = ibis.ifelse(true_expr, ibis.literal(True), ibis.ifelse(false_expr, ibis.literal(False), ibis.literal(None)))
        return table.mutate(**{self.output_column: bool_expr})


class ToNumeric(Transform):
    """Cast a string or other column to a numeric type.

    Parameters
    ----------
    source_column
        The source column. May be a ``Column`` descriptor or a string.
    dtype
        Target numeric type, e.g. ``"int64"`` or ``"float64"``.
    errors
        Behavior when a value cannot be converted:

        - ``"raise"`` (default): raise an error.
        - ``"coerce"``: replace invalid values with ``null``.

        ``"coerce"`` requires a backend native override because Ibis cast
        expressions do not support graceful failure.
    output
        Name of the resulting column. If omitted, inferred from the owning
        ``Column`` descriptor.

    Examples
    --------
    >>> class Product(RedMeta):
    ...     price_str = Column(str)
    ...     price = Column(float, transform=ToNumeric(price_str, "float64"))

    """

    def __init__(
        self,
        source_column: Column | str,
        dtype: str = "int64",
        *,
        errors: str = "raise",
        output: str = "",
    ) -> None:
        """Initialize a ``ToNumeric`` transformation.

        Parameters
        ----------
        source_column
            Source column.
        dtype
            Target Ibis data type.
        errors
            ``"raise"`` or ``"coerce"``.
        output
            Name of the output column.
        """
        if errors not in {"raise", "coerce"}:
            raise ValueError("errors must be 'raise' or 'coerce'")
        self.source_column = source_column
        self.dtype = dtype
        self.errors = errors
        self._output = output

    @property
    def output_column(self) -> str:
        """Return the name of the output column."""
        return self._output

    def set_output_column(self, name: str) -> None:
        """Set the output column name from the owning column."""
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that casts the source column to numeric.

        Parameters
        ----------
        table
            Ibis table expression.

        Returns
        -------
        ibis.Table
            Table expression with the cast column.

        Raises
        ------
        NotImplementedError
            If ``errors`` is ``"coerce"`` and no backend override is used.
        """
        if self.errors == "coerce":
            raise NotImplementedError(
                "ToNumeric with errors='coerce' requires a backend native override"
            )
        source = self.input_columns()[0]
        return table.mutate(**{self.output_column: table[source].cast(self.dtype)})


class RegexExtract(Transform):
    r"""Extract a substring matching a regular expression.

    Parameters
    ----------
    source_column
        The source string column. May be a ``Column`` descriptor or a string.
    pattern
        Regular expression pattern. Must contain at least one capture group
        if ``group > 0``.
    group
        Capture group index to return. ``0`` returns the full match.
    output
        Name of the resulting column. If omitted, inferred from the owning
        ``Column`` descriptor.

    Examples
    --------
    >>> class Log(RedMeta):
    ...     message = Column(str)
    ...     error_code = Column(str, transform=RegexExtract(message, r"ERROR-(\d+)", group=1))

    """

    def __init__(
        self,
        source_column: Column | str,
        pattern: str,
        group: int = 0,
        output: str = "",
    ) -> None:
        """Initialize a ``RegexExtract`` transformation.

        Parameters
        ----------
        source_column
            Source string column.
        pattern
            Regular expression pattern.
        group
            Capture group index.
        output
            Name of the output column.
        """
        self.source_column = source_column
        self.pattern = pattern
        self.group = group
        self._output = output

    @property
    def output_column(self) -> str:
        """Return the name of the output column."""
        return self._output

    def set_output_column(self, name: str) -> None:
        """Set the output column name from the owning column."""
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that extracts the regex group.

        If the pattern does not match, the result is ``null`` rather than an
        empty string. This behavior is normalized across backends.

        Parameters
        ----------
        table
            Ibis table expression.

        Returns
        -------
        ibis.Table
            Table expression with the extracted column.
        """
        source = table[self.input_columns()[0]]
        extracted = source.re_extract(self.pattern, self.group)
        matched = source.re_search(self.pattern)
        value = ibis.ifelse(matched, extracted, ibis.literal(None))
        return table.mutate(**{self.output_column: value})


@dataclass
class OutputField:
    """Describe a single output field produced by an explode transform.

    ``OutputField`` is a factory specification consumed by :func:`ExplodeList`
    and :func:`ExplodeDict`. Each instance becomes a :class:`Column` after the
    factory unpacks it on a ``RedMeta`` class.

    Parameters
    ----------
    name
        Name of the resulting column.
    dtype
        Logical data type of the resulting column.
    source_key
        For :func:`ExplodeDict`, the key in the source dictionary when it
        differs from ``name``. If omitted, ``name`` is used as the dictionary
        key.

    Notes
    -----
    ``OutputField`` is intentionally not a subclass of :class:`Column`. They
    share ``name`` and ``dtype`` but have different responsibilities: a
    ``Column`` is a descriptor on a schema, while ``OutputField`` is only a
    constructor argument for columns produced by explode transforms. See
    ``PROJECT.md`` for the design rationale.

    """

    name: str
    dtype: type | str
    source_key: str | None = None


class _ExplodeListTransform(Transform):
    """Batch transform that extracts multiple list positions at once."""

    def __init__(self, source_column: Column | str, outputs: list[OutputField]) -> None:
        """Initialize the batch list explode transform.

        Parameters
        ----------
        source_column
            Source list/array column.
        outputs
            Output field specifications, one per list position.
        """
        self.source_column = source_column
        self.outputs = outputs

    @property
    def output_column(self) -> str:
        """Return the first output column name.

        This property exists for API compatibility with the base class. The
        transform produces multiple columns.
        """
        return self.outputs[0].name

    def set_output_column(self, name: str) -> None:
        """No-op: output columns are explicitly provided."""

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Return an Ibis expression that extracts list elements.

        Parameters
        ----------
        table
            Ibis table expression.

        Returns
        -------
        ibis.Table
            Table expression with the extracted columns.
        """
        source = table[self.input_columns()[0]]
        mutations = {
            field.name: source[i]
            for i, field in enumerate(self.outputs)
        }
        return table.mutate(**mutations)


def ExplodeList(
    source_column: Column | str,
    outputs: list[OutputField],
) -> tuple[Column, ...]:
    """Extract list elements into named output columns.

    Returns a tuple of :class:`Column` descriptors that can be unpacked on a
    ``RedMeta`` class. The list is processed once by a single batch transform
    attached to the first returned column.

    Parameters
    ----------
    source_column
        The source list/array column. May be a ``Column`` descriptor or a
        string.
    outputs
        Output field specifications, one per list position.

    Returns
    -------
    tuple[Column, ...]
        Column descriptors in the same order as ``outputs``.

    Examples
    --------
    >>> class Order(RedMeta):
    ...     items = Column("array")
    ...     sku_1, qty_1, sku_2, qty_2 = ExplodeList(
    ...         items,
    ...         outputs=[
    ...             OutputField("sku_1", str),
    ...             OutputField("qty_1", int),
    ...             OutputField("sku_2", str),
    ...             OutputField("qty_2", int),
    ...         ],
    ...     )

    """
    if not outputs:
        raise ValueError("ExplodeList requires at least one OutputField")

    columns: list[Column] = []
    for index, field in enumerate(outputs):
        transform = _ExplodeListTransform(source_column, outputs) if index == 0 else None
        column = Column(field.dtype, transform=transform)
        column.name = field.name
        columns.append(column)
    return tuple(columns)


class _ExplodeDictTransform(Transform):
    """Batch transform that extracts multiple dictionary keys at once."""

    def __init__(
        self,
        source_column: Column | str,
        outputs: list[OutputField],
        *,
        on_missing: str = "null",
    ) -> None:
        """Initialize the batch dict explode transform.

        Parameters
        ----------
        source_column
            Source dictionary column.
        outputs
            Output field specifications.
        on_missing
            ``"null"`` to insert null for missing keys, ``"raise"`` to raise.
        """
        self.source_column = source_column
        self.outputs = outputs
        self.on_missing = on_missing

    @property
    def output_column(self) -> str:
        """Return the first output column name.

        This property exists for API compatibility with the base class. The
        transform produces multiple columns.
        """
        return self.outputs[0].name

    def set_output_column(self, name: str) -> None:
        """No-op: output columns are explicitly provided."""

    def input_columns(self) -> list[str]:
        """Return the source column name."""
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        """Raise because dict explosion requires backend-specific handling.

        Parameters
        ----------
        table
            Ibis table expression.

        Raises
        ------
        NotImplementedError
            Always, because Ibis does not provide a portable dict-to-columns
            operation. Backends must register a native override.
        """
        raise NotImplementedError(
            "ExplodeDict requires a backend native override"
        )


def ExplodeDict(
    source_column: Column | str,
    outputs: list[OutputField],
    *,
    on_missing: str = "null",
) -> tuple[Column, ...]:
    """Extract dictionary values into named output columns.

    Returns a tuple of :class:`Column` descriptors that can be unpacked on a
    ``RedMeta`` class. The dictionary is processed once by a single batch
    transform attached to the first returned column.

    Parameters
    ----------
    source_column
        The source dictionary column. May be a ``Column`` descriptor or a
        string.
    outputs
        Output field specifications. The dictionary key defaults to the
        column name; use ``source_key`` to override it.
    on_missing
        Behavior when a key is missing: ``"null"`` inserts ``null``,
        ``"raise"`` raises an error.

    Returns
    -------
    tuple[Column, ...]
        Column descriptors in the same order as ``outputs``.

    Examples
    --------
    >>> class Order(RedMeta):
    ...     raw = Column("map")
    ...     country, channel = ExplodeDict(
    ...         raw,
    ...         outputs=[
    ...             OutputField("country", str),
    ...             OutputField("channel", str, source_key="ch"),
    ...         ],
    ...     )

    """
    if not outputs:
        raise ValueError("ExplodeDict requires at least one OutputField")
    if on_missing not in {"null", "raise"}:
        raise ValueError("on_missing must be 'null' or 'raise'")

    columns: list[Column] = []
    for index, field in enumerate(outputs):
        transform = (
            _ExplodeDictTransform(source_column, outputs, on_missing=on_missing)
            if index == 0
            else None
        )
        column = Column(field.dtype, transform=transform)
        column.name = field.name
        columns.append(column)
    return tuple(columns)


def _column_name(column: Column | str) -> str:
    """Resolve a ``Column`` descriptor or string to a column name.

    Parameters
    ----------
    column
        Either a ``Column`` descriptor or a plain column name string.

    Returns
    -------
    str
        The resolved column name.

    Raises
    ------
    TypeError
        If ``column`` is neither a ``Column`` nor a ``str``.
    """
    if isinstance(column, str):
        return column
    if hasattr(column, "name"):
        return str(column.name)
    raise TypeError(f"Expected Column or str, got {type(column).__name__}")
