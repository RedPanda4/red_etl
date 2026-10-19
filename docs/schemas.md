# Schemas

Schemas in `red-etl` are declared as Python classes. This gives you IDE autocompletion, refactor safety, and a single source of truth for the shape of your data.

---

## `RedMeta`

`RedMeta` is the base class for every table or DataFrame schema.

```python
from red_etl import RedMeta, Column

class User(RedMeta):
    id = Column(int, primary_key=True)
    name = Column(str, nullable=False)
    age = Column(int)
```

`RedMeta` classes are not meant to be instantiated — they describe tables, not rows.

---

## `Column`

`Column` describes a single column in a schema.

```python
Column(dtype, *, nullable=True, primary_key=False, description="", transform=None)
```

| Parameter | Description |
|-----------|-------------|
| `dtype` | Logical data type. Use Python types (`int`, `str`, `float`, `bool`) or backend-neutral strings (`"date"`, `"datetime"`, `"array"`, `"map"`). |
| `nullable` | Whether the column may contain missing values. Default `True`. |
| `primary_key` | Whether the column is part of the primary key. Default `False`. |
| `description` | Optional human-readable description. |
| `transform` | Optional `Transform` that produces this column from other columns. |

Examples:

```python
class Event(RedMeta):
    event_id = Column(int, primary_key=True)
    happened_at = Column("datetime")
    revenue = Column(float, nullable=True, description="Revenue in EUR")
```

---

## Referencing columns

Inside a schema you can reference other `Column` descriptors directly. This avoids string-based lookups and lets your IDE autocomplete column names.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import ConcatColumns

class User(RedMeta):
    first_name = Column(str)
    last_name = Column(str)
    full_name = Column(
        str,
        transform=ConcatColumns([first_name, last_name], separator=" "),
    )
```

`ConcatColumns([first_name, last_name], ...)` is equivalent to `ConcatColumns(["first_name", "last_name"], ...)`, but type-safe.

---

## Inspecting a schema

`RedMeta` provides class methods for introspection:

```python
User.columns()
# {'id': Column(name='id', dtype=<class 'int'>), ...}

User.column_names()
# ['id', 'name', 'age']

User.get_column("name")
# Column(name='name', dtype=<class 'str'>)

User.has_column("email")
# False
```

---

## Column order

Columns are returned in the order they are defined on the class. This order is preserved when the schema is applied to data.

---

## Nullability and primary keys

`nullable` and `primary_key` are metadata flags. They are consumed by validation and may be used by future pipeline features; they do not change how `apply_transforms` builds the Ibis expression.

---

## Next steps

- See the full list of built-in [transforms](transforms.md).
- Learn how to run schemas on different [backends](backends.md).
