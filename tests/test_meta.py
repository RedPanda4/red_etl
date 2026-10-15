"""Unit tests for :mod:`red_etl.meta`."""

import pytest

from red_etl import Column, RedMeta


def test_redmeta_collects_columns() -> None:
    """RedMeta should collect Column descriptors in definition order."""

    class User(RedMeta):
        id = Column(int, primary_key=True)
        name = Column(str, nullable=False)
        age = Column(int)

    columns = User.columns()

    assert list(columns.keys()) == ["id", "name", "age"]
    assert columns["id"].dtype is int
    assert columns["name"].nullable is False


def test_redmeta_column_names() -> None:
    """column_names should return declared column names in order."""

    class User(RedMeta):
        id = Column(int)
        name = Column(str)

    assert User.column_names() == ["id", "name"]


def test_redmeta_get_column() -> None:
    """get_column should return the requested Column descriptor."""

    class User(RedMeta):
        id = Column(int)

    assert User.get_column("id").name == "id"


def test_redmeta_get_missing_column_raises() -> None:
    """get_column should raise KeyError for unknown columns."""

    class User(RedMeta):
        id = Column(int)

    with pytest.raises(KeyError, match="not_found"):
        User.get_column("not_found")


def test_redmeta_has_column() -> None:
    """has_column should report whether a column exists."""

    class User(RedMeta):
        id = Column(int)

    assert User.has_column("id") is True
    assert User.has_column("name") is False


def test_redmeta_cannot_be_instantiated() -> None:
    """RedMeta classes describe schemas and should not be instantiated."""

    class User(RedMeta):
        id = Column(int)

    with pytest.raises(TypeError):
        User()


def test_redmeta_columns_are_independent_between_subclasses() -> None:
    """Each RedMeta subclass should have its own column set."""

    class User(RedMeta):
        id = Column(int)

    class Order(RedMeta):
        order_id = Column(int)

    assert User.column_names() == ["id"]
    assert Order.column_names() == ["order_id"]


def test_redmeta_inheritance_does_not_leak_columns() -> None:
    """Subclasses should start with an empty column set, not inherit parent's."""

    class Base(RedMeta):
        id = Column(int)

    class Child(Base):
        name = Column(str)

    # Current design: each class only collects columns declared directly on it.
    assert Child.column_names() == ["name"]
    assert Base.column_names() == ["id"]
