# Adding a backend native override

This guide shows how to add a **native override** for a transform on a specific backend. Native overrides are used when Ibis does not support an operation well on a given engine, or when a backend-specific implementation is faster or more correct.

> **Rule of thumb:** implement every transform as an Ibis expression first. Only add a native override if you have a concrete reason (bug, missing feature, or significant performance gain).

---

## What you need

A native override is a function with this signature:

```python
def native_impl(transform: Transform, data: NativeDataType) -> NativeDataType:
    ...
```

- `transform` — the transform object that describes the operation.
- `data` — the dataset in the backend's native format (for example a `pandas.DataFrame`).
- The return value must be the transformed dataset in the same native format.

You then register the function on the backend's `native_overrides` registry, keyed by the transform type.

---

## How the pipeline uses overrides

`apply_transforms` does the following:

1. Collects all transforms declared on the schema.
2. Asks the backend whether it has a native override for each transform via `backend.supports_native(transform)`.
3. Groups consecutive transforms that do **not** have native overrides into one Ibis expression batch.
4. Builds each Ibis batch as a single expression, then applies the native override by materializing to the backend's native format, converting back to an Ibis table, and continuing with the next batch.

This keeps the common path as one big Ibis expression and only splits the plan where necessary.

---

## Example: native `ConcatColumns` for Pandas

Suppose you want to override `ConcatColumns` on `PandasBackend` to use `str.cat` and handle missing values differently.

### 1. Write the native function

Create or edit `red_etl/backends/pandas.py`:

```python
import pandas as pd

from red_etl.transforms import ConcatColumns


def pandas_concat_columns(transform: ConcatColumns, data: pd.DataFrame) -> pd.DataFrame:
    """Concatenate columns using Pandas native string methods."""
    columns = transform.input_columns()
    separator = transform.separator
    output = transform.output_column

    data[output] = data[columns[0]].str.cat(
        others=data[columns[1:]],
        sep=separator,
        na_rep="",
    )
    return data
```

### 2. Register the override

Register the function inside `PandasBackend.__init__`:

```python
class PandasBackend(Backend):
    name = "pandas"

    def __init__(self) -> None:
        super().__init__()
        self.native_overrides[ConcatColumns] = pandas_concat_columns
```

### 3. Use it

Now `PandasBackend` will use the native implementation for `ConcatColumns`:

```python
from red_etl import Column, ConcatColumns, RedMeta, apply_transforms
from red_etl.backends.pandas import PandasBackend


class User(RedMeta):
    first_name = Column(str)
    last_name = Column(str)
    full_name = Column(
        str,
        transform=ConcatColumns([first_name, last_name], separator=" "),
    )


df = pd.DataFrame({"first_name": ["Alice"], "last_name": ["Smith"]})
result = apply_transforms(df, User, PandasBackend())
```

---

## Batch transforms

Some transforms produce multiple columns at once. `ExplodeList` and `ExplodeDict` are factory functions that create a batch transform on the first returned `Column`. Register the native override on the batch transform class, not on the factory function.

```python
from red_etl.transforms import _ExplodeListTransform


def pandas_explode_list(transform: _ExplodeListTransform, data: pd.DataFrame) -> pd.DataFrame:
    source = transform.input_columns()[0]
    outputs = transform.outputs

    for i, field in enumerate(outputs):
        data[field.name] = data[source].apply(
            lambda x: x[i] if x is not None else None
        )
    return data


class PandasBackend(Backend):
    def __init__(self) -> None:
        super().__init__()
        self.native_overrides[_ExplodeListTransform] = pandas_explode_list
```

---

## Testing a native override

Add a test in `tests/test_backends.py` or `tests/test_pipeline.py`:

```python
import pandas as pd
from red_etl import Column, ConcatColumns, RedMeta, apply_transforms
from red_etl.backends.pandas import PandasBackend


def test_pandas_backend_native_concat_columns() -> None:
    class User(RedMeta):
        first_name = Column(str)
        last_name = Column(str)
        full_name = Column(
            str,
            transform=ConcatColumns([first_name, last_name], separator=" "),
        )

    backend = PandasBackend()
    data = pd.DataFrame({"first_name": ["Alice"], "last_name": ["Smith"]})
    result = apply_transforms(data, User, backend)

    assert result.execute()["full_name"].tolist() == ["Alice Smith"]
```

---

## Where to add native overrides

Keep the override function in the backend file where it belongs:

| Backend | File |
|---------|------|
| Pandas | `red_etl/backends/pandas.py` |
| Polars | `red_etl/backends/polars.py` |
| DuckDB | `red_etl/backends/duckdb.py` |
| Spark  | `red_etl/backends/spark.py` |

Do not put native implementations in `red_etl/transforms.py`. Transforms must remain backend-agnostic Ibis expressions by default.

---

## Summary

1. Implement the transform as an Ibis expression in `red_etl/transforms.py`.
2. If Ibis support is weak on a backend, write a native function in that backend's file.
3. Register it in `backend.native_overrides[TransformClass]`.
4. Test the override in the corresponding test file.

The rest of the framework stays unchanged.
