# Adding a transform

This guide shows how to add a new backend-agnostic transform to `red_etl/transforms.py`. Transforms are the building blocks that derive or clean columns in a `RedMeta` schema.

> **Rule of thumb:** implement every transform as an Ibis expression first. Only add a backend native override if Ibis support is weak or buggy for a specific engine.

---

## What a transform looks like

A transform is a subclass of `Transform` that implements three things:

- `input_columns()` — names of the columns it reads from.
- `output_column` — name of the column it produces.
- `to_ibis(table)` — an Ibis expression that applies the transformation.

Here is a minimal example:

```python
import ibis
from red_etl.transforms import Transform

class UpperCase(Transform):
    """Convert a string column to upper case."""

    def __init__(self, source_column, output: str = ""):
        self.source_column = source_column
        self._output = output

    @property
    def output_column(self) -> str:
        return self._output

    def set_output_column(self, name: str) -> None:
        if not self._output:
            self._output = name

    def input_columns(self) -> list[str]:
        return [_column_name(self.source_column)]

    def to_ibis(self, table: ibis.Table) -> ibis.Table:
        source = self.input_columns()[0]
        return table.mutate(**{self.output_column: table[source].upper()})
```

Use the existing helper `_column_name` to resolve `Column` descriptors or plain strings to column names.

---

## Register the output column name

When a transform is assigned to a `Column` on a `RedMeta` class, `RedMeta.__init_subclass__` calls `transform.set_output_column(name)` with the attribute name. If the user did not provide an explicit `output`, use that name:

```python
def set_output_column(self, name: str) -> None:
    if not self._output:
        self._output = name
```

---

## Add the transform to the public API

If the transform is meant to be public, export it from `red_etl/__init__.py`:

```python
from red_etl.transforms import (
    # ... existing transforms
    UpperCase,
)

__all__ = [
    # ... existing entries
    "UpperCase",
]
```

---

## Test the transform

Add a test in `tests/test_transforms.py` or `tests/test_pipeline.py`:

```python
import pandas as pd
from red_etl import Column, RedMeta, apply_transforms
from red_etl.backends.pandas import PandasBackend
from red_etl.transforms import UpperCase


def test_uppercase_transform() -> None:
    class User(RedMeta):
        name = Column(str)
        name_upper = Column(str, transform=UpperCase(name))

    df = pd.DataFrame({"name": ["Alice", "Bob"]})
    result = apply_transforms(df, User, PandasBackend())

    assert result.execute()["name_upper"].tolist() == ["ALICE", "BOB"]
```

---

## Summary

1. Subclass `Transform` in `red_etl/transforms.py`.
2. Implement `input_columns()`, `output_column`, and `to_ibis(table)`.
3. Handle `set_output_column` so the output name defaults to the attribute name.
4. Export the transform from `red_etl/__init__.py` if public.
5. Add unit tests.

If a backend needs special handling, see [Adding a backend native override](adding-native-overrides.md).
