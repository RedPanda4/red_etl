"""Base ``RedMeta`` class for declaring table schemas."""

from __future__ import annotations

from typing import TypeVar

from red_etl.column import Column

T = TypeVar("T", bound="RedMeta")


class RedMeta:
    """Base class for declaring table or DataFrame schemas.

    Subclasses define columns as class attributes using the :class:`Column`
    descriptor. ``RedMeta`` collects those descriptors and exposes them as a
    ordered mapping, making the schema introspectable without requiring
    string-based column lookups.

    Examples
    --------
    >>> from red_etl import RedMeta, Column
    >>> class User(RedMeta):
    ...     id = Column(int, primary_key=True)
    ...     name = Column(str, nullable=False)
    >>> User.columns()
    {'id': Column(name='id', dtype=<class 'int'>), ...}

    """

    def __init_subclass__(cls, **kwargs: dict[str, object]) -> None:
        """Collect ``Column`` descriptors when a subclass is created.

        This hook is executed automatically for every ``RedMeta`` subclass.
        It stores the column descriptors in definition order on the class so
        that they can be retrieved later via :meth:`columns`. If a column has
        an associated transformation without an explicit output name, the
        output name is set to the column name.

        Parameters
        ----------
        **kwargs
            Extra keyword arguments passed to the class definition.
        """
        super().__init_subclass__(**kwargs)
        cls._columns: dict[str, Column] = {}
        for name, value in cls.__dict__.items():
            if isinstance(value, Column):
                if value.transform is not None:
                    value.transform.set_output_column(name)
                cls._columns[name] = value

    @classmethod
    def columns(cls: type[T]) -> dict[str, Column]:
        """Return all ``Column`` descriptors declared on this schema.

        The returned dictionary preserves the definition order of the columns
        on the subclass.

        Returns
        -------
        dict[str, Column]
            A mapping from column name to ``Column`` descriptor.
        """
        return dict(cls._columns)

    @classmethod
    def column_names(cls: type[T]) -> list[str]:
        """Return the names of all columns declared on this schema.

        Returns
        -------
        list[str]
            A list of column names in definition order.
        """
        return list(cls._columns.keys())

    @classmethod
    def get_column(cls: type[T], name: str) -> Column:
        """Retrieve a single ``Column`` descriptor by name.

        Parameters
        ----------
        name
            The name of the column to retrieve.

        Returns
        -------
        Column
            The matching column descriptor.

        Raises
        ------
        KeyError
            If no column with the given name exists on the schema.
        """
        try:
            return cls._columns[name]
        except KeyError as exc:
            raise KeyError(f"Column {name!r} not found on {cls.__name__}") from exc

    @classmethod
    def has_column(cls: type[T], name: str) -> bool:
        """Check whether a column with the given name exists on the schema.

        Parameters
        ----------
        name
            The column name to check.

        Returns
        -------
        bool
            ``True`` if the column exists, otherwise ``False``.
        """
        return name in cls._columns

    def __init__(self) -> None:
        """Raise an error if a user tries to instantiate ``RedMeta`` directly.

        ``RedMeta`` classes describe table schemas; they are not meant to hold
        row data. Instances should not be created.

        Raises
        ------
        TypeError
            Always, because ``RedMeta`` cannot be instantiated.
        """
        raise TypeError("RedMeta classes cannot be instantiated.")
