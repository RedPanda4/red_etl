# Quick start

Install `red-etl`, declare a schema, and run your first transformation.

---

## Installation

The core package has no execution backend. Install at least one backend to run transforms.

```bash
# Core only (no execution backend)
pip install red-etl

# With Pandas support
pip install "red-etl[pandas]"

# With Polars support
pip install "red-etl[polars]"

# With both
pip install "red-etl[pandas,polars]"
```

Other optional extras:

| Extra | Adds |
|-------|------|
| `duckdb` | DuckDB execution engine (planned backend). |
| `sql` | SQL sources/sinks via SQLAlchemy. |
| `excel` | Excel sources/sinks via `openpyxl`. |
| `validation` | Pandera value validation. |
| `all` | Everything above. |

---

## Your first schema

A schema is a Python class that inherits from `RedMeta`. Each column is a `Column` descriptor with a type and optional transformation.

```python
from red_etl import Column, RedMeta, apply_transforms
from red_etl.backends.pandas import PandasBackend
from red_etl.transforms import ConcatColumns


class User(RedMeta):
    first_name = Column(str)
    last_name = Column(str)
    full_name = Column(
        str,
        transform=ConcatColumns([first_name, last_name], separator=" "),
    )
```

`first_name` and `last_name` are copied through unchanged. `full_name` is produced by concatenating the two source columns.

---

## Run a transformation

Pass a DataFrame, the schema, and a backend to `apply_transforms`. The result is a lazy Ibis `Table` expression.

```python
import pandas as pd

df = pd.DataFrame({
    "first_name": ["Alice", "Bob"],
    "last_name": ["Smith", "Jones"],
})

result = apply_transforms(df, User, PandasBackend())
print(result.execute()["full_name"].tolist())
# ['Alice Smith', 'Bob Jones']
```

You can also start from an Ibis table:

```python
import ibis

table = ibis.memtable(df)
result = apply_transforms(table, User, PandasBackend())
```

---

## Use a different backend

The same schema works with any supported backend. Just change the backend instance:

```python
import polars as pl
from red_etl.backends.polars import PolarsBackend

pl_df = pl.DataFrame({
    "first_name": ["Alice", "Bob"],
    "last_name": ["Smith", "Jones"],
})

result = apply_transforms(pl_df, User, PolarsBackend())
print(result.to_polars()["full_name"].to_list())
# ['Alice Smith', 'Bob Jones']
```

See [Backends](backends.md) for the full list and selection tips.

---

## Next steps

- Read about [schemas](schemas.md) and all available [transforms](transforms.md).
- Learn how to read and write files with the [I/O adapters](io.md).
- See a complete Bronze → Silver example in [`examples/explode_usage.py`](../examples/explode_usage.py).
