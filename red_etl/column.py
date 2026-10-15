"""Column descriptor used to declare typed attributes on ``RedMeta`` classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from red_etl.transforms import Transform


class Column:
    """Describe a single column inside a ``RedMeta`` table schema.

    A ``Column`` instance is intended to be used as a class attribute on a
    ``RedMeta`` subclass. It captures metadata such as the logical data type,
    whether the column is nullable, whether it is a primary key and an
    optional human-readable description.

    Because ``Column`` implements the descriptor protocol, assigning it to a
    class attribute lets it discover its own name when the parent class is
    created.

    Parameters
    ----------
    dtype
        The logical data type of the column. This may be a Python built-in
        type such as ``str`` or ``int``, or a backend-neutral string such as
        ``"datetime"`` when no single Python type is sufficient.
    nullable
        ``True`` if the column is allowed to contain null/missing values.
    primary_key
        ``True`` if the column is part of the primary key of the table.
    description
        An optional human-readable description of the column.
    transform
        An optional transformation that produces this column from other
        columns. When provided, the framework applies the transformation
        during the cleaning step instead of copying the column from the
        source as-is.

    Examples
    --------
    >>> from red_etl import Column
    >>> class User:
    ...     id = Column(int, primary_key=True)
    ...     name = Column(str, nullable=False)

    """

    def __init__(
        self,
        dtype: type | str,
        *,
        nullable: bool = True,
        primary_key: bool = False,
        description: str = "",
        transform: Transform | None = None,
    ) -> None:
        """Initialize a ``Column`` descriptor.

        Parameters
        ----------
        dtype
            Logical data type of the column.
        nullable
            Whether null values are allowed.
        primary_key
            Whether the column is part of the primary key.
        description
            Optional description of the column.
        transform
            Optional transformation applied to derive this column.
        """
        self.dtype = dtype
        self.nullable = nullable
        self.primary_key = primary_key
        self.description = description
        self.transform = transform
        self.name: str = ""

    def __set_name__(self, owner: type, name: str) -> None:
        """Record the attribute name used on the parent class.

        This method is called automatically by Python when the descriptor is
        assigned as a class attribute. It stores the public name so that the
        column can be referenced later without relying on string lookups.

        Parameters
        ----------
        owner
            The class that owns this descriptor.
        name
            The attribute name used for this descriptor on ``owner``.
        """
        self.name = name

    def __get__(self, instance: object | None, owner: type) -> Column:
        """Return the descriptor itself when accessed via class or instance.

        Accessing ``User.id`` returns the ``Column`` object, enabling
        column-aware transformations and IDE autocompletion.

        Parameters
        ----------
        instance
            The instance the descriptor is accessed on, or ``None`` when
            accessed via the class.
        owner
            The class that owns the descriptor.

        Returns
        -------
        Column
            The column descriptor itself.
        """
        return self

    def __set__(self, instance: object, value: Any) -> None:
        """Prevent accidental mutation of column definitions on instances.

        Parameters
        ----------
        instance
            The instance on which the assignment is attempted.
        value
            The value being assigned.

        Raises
        ------
        AttributeError
            Always, because column metadata is read-only.
        """
        raise AttributeError("Column metadata is read-only.")

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the column.

        Returns
        -------
        str
            A string showing the column name and data type.
        """
        return f"Column(name={self.name!r}, dtype={self.dtype!r})"
