# Adding a Native Transformation Override

This guide shows how to add a **native override** for a transformation on a
specific backend. Native overrides are used when Ibis does not support an
operation well on a given engine, or when you can write a faster
backend-specific implementation.

> **Rule of thumb:** implement every transform as an Ibis expression first.
> Only add a native override if you have a concrete reason (bug, missing
> feature, or significant performance gain).

---

## What you need

A native override is a function with this signature:

```python
def native_impl(transform: Transform, data: NativeDataType) -> NativeDataType:
    ...
```

- `transform` — the transform object that describes the operation.
- `data` — the dataset in the backend's native format (for example a
  `pandas.DataFrame`).
- The return value must be the transformed dataset in the same native format.

You then register the function on the backend's `native_overrides` registry,
keyed by the transform type.

---

## Example: native `ConcatColumns` for Pandas

Suppose you want to override `ConcatColumns` on `PandasBackend` because you
prefer `str.cat` and need to handle missing values differently.

### 1. Write the native function

Create or edit `red_etl/backends/pandas.py`:

```python
import pandas as pd

from red_etl.transforms import ConcatColumns


def pandas_concat_columns(transform: ConcatColumns, data: pd.DataFrame) -> pd.DataFrame:
    """Concatenate columns using Pandas native string methods.

    Parameters
    ----------
    transform
        The ``ConcatColumns`` transform being applied.
    data
        Input Pandas DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with the new concatenated column.
    """
    columns = transform.input_columns()
    separator = transform.separator
    output = transform.output_column

    # Build a Series that concatenates all columns with the separator.
    data[output] = data[columns[0]].str.cat(
        others=data[columns[1:]],
        sep=separator,
        na_rep="",
    )
    return data
```

### 2. Register the override in the backend

Still in `red_etl/backends/pandas.py`, register the function inside
`PandasBackend.__init__`:

```python
class PandasBackend(Backend):
    name = "pandas"

    def __init__(self) -> None:
        super().__init__()
        self.native_overrides[ConcatColumns] = pandas_concat_columns
```

### 3. Use it

Now when you run a pipeline with `PandasBackend`, `ConcatColumns` will use
your native implementation instead of the Ibis expression:

```python
import ibis
from red_etl import Column, ConcatColumns, RedMeta, apply_transforms
from red_etl.backends.pandas import PandasBackend


class User(RedMeta):
    first_name = Column(str)
    last_name = Column(str)
    full_name = Column(
        str,
        transform=ConcatColumns([first_name, last_name], separator=" "),
    )


table = ibis.memtable({
    "first_name": ["Alice", "Bob"],
    "last_name": ["Smith", "Jones"],
})

result = apply_transforms(table, User, PandasBackend())
print(result.execute()["full_name"].tolist())
# ['Alice Smith', 'Bob Jones']
```

---

## How the pipeline decides what to run

`apply_transforms` in `red_etl.pipeline` receives an Ibis ``Table`` and does
the following:

1. Collect all transforms declared on the `RedMeta` schema.
2. Ask the backend whether it has a native override for each transform via
   `backend.supports_native(transform)`.
3. Group consecutive transforms that do **not** have native overrides into
   one Ibis expression batch.
4. Build each Ibis batch as a single expression, then apply the native
   override by materializing to the backend's native format and converting
   back to an Ibis table, then continue with the next Ibis batch.

This means the common path stays as one big Ibis expression, and native
overrides only split the plan where necessary.

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
    data = pd.DataFrame({
        "first_name": ["Alice"],
        "last_name": ["Smith"],
    })

    result = apply_transforms(data, User, backend)

    assert result["full_name"].tolist() == ["Alice Smith"]
```

---

## Where to add native overrides

Keep the override function in the same backend file where it belongs:

| Backend | File |
|---------|------|
| Pandas | `red_etl/backends/pandas.py` |
| Polars | `red_etl/backends/polars.py` |
| DuckDB | `red_etl/backends/duckdb.py` |
| Spark | `red_etl/backends/spark.py` |

Do not put native implementations in `red_etl/transforms.py`. Transforms must
remain backend-agnostic Ibis expressions by default.

---

## Example: a more complex override

Some transforms produce multiple columns at once. For example, `ExplodeList`
and `ExplodeDict` are factory functions that create a batch transform on the
first returned `Column`. The native override is registered on that batch
transform class, not on the factory function.

```python
# red_etl/backends/pandas.py

from red_etl.transforms import _ExplodeListTransform


def pandas_explode_list(transform: _ExplodeListTransform, data: pd.DataFrame) -> pd.DataFrame:
    source = transform.input_columns()[0]
    outputs = transform.outputs  # list[OutputField]

    for i, field in enumerate(outputs):
        data[field.name] = data[source].apply(lambda x: x[i] if x is not None else None)
    return data


class PandasBackend(Backend):
    def __init__(self) -> None:
        super().__init__()
        self.native_overrides[ConcatColumns] = pandas_concat_columns
        self.native_overrides[_ExplodeListTransform] = pandas_explode_list
```

The pipeline will automatically split the Ibis plan around the batch transform
and use the native Pandas implementation for that step only.

---

## Summary

1. Implement the transform as an Ibis expression in `red_etl/transforms.py`.
2. If Ibis support is weak on a backend, write a native function in that
   backend's file.
3. Register it in `backend.native_overrides[TransformClass]`.
4. Test the override in the corresponding test file.

The rest of the framework stays unchanged.
