"""Unit tests for :mod:`red_etl.column`."""

import pytest

from red_etl.column import Column


def test_column_stores_metadata() -> None:
    """A Column should store dtype, nullability, primary-key and description."""
    column = Column(int, nullable=False, primary_key=True, description="User id")

    assert column.dtype is int
    assert column.nullable is False
    assert column.primary_key is True
    assert column.description == "User id"


def test_column_descriptor_receives_name() -> None:
    """When assigned as a class attribute, the Column learns its public name."""

    class User:
        id = Column(int)

    assert User.id.name == "id"


def test_column_is_read_only_on_instance() -> None:
    """Assigning to a Column attribute on an instance should raise."""

    class User:
        id = Column(int)

    user = object.__new__(User)

    with pytest.raises(AttributeError):
        user.id = 1


def test_column_repr() -> None:
    """Column repr should include its name and dtype."""

    class User:
        age = Column(int)

    assert "age" in repr(User.age)
    assert "int" in repr(User.age)
