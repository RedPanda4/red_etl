# Backends

A backend is the execution engine that runs your transformations. `red-etl` keeps schemas backend-agnostic, so you can pick the engine at runtime.

---

## Available backends

| Backend | Module | Dependency | Status |
|---------|--------|------------|--------|
| Pandas | `red_etl.backends.pandas` | `pandas` | Implemented |
| Polars | `red_etl.backends.polars` | `polars` | Implemented |
| DuckDB | `red_etl.backends.duckdb` | `duckdb` | Planned |
| Spark  | `red_etl.backends.spark`  | `pyspark` | Planned |

Importing a backend module without its dependency raises `ImportError` with an installation hint.

---

## Pandas backend

```python
from red_etl.backends.pandas import PandasBackend

backend = PandasBackend()
result = apply_transforms(df, User, backend)
```

- Converts DataFrames with `ibis.memtable`.
- Returns `pandas.DataFrame` when the expression is executed.
- Supports CSV, Parquet, SQL, and Excel I/O.

Native overrides:

- `ExplodeList`
- `ExplodeDict`
- `ToNumeric` with `errors="coerce"`

---

## Polars backend

```python
from red_etl.backends.polars import PolarsBackend

backend = PolarsBackend()
result = apply_transforms(df, User, backend)
```

- Uses the `ibis.polars` backend.
- Returns `polars.DataFrame` when the expression is executed.
- Supports CSV and Parquet I/O.

Native overrides:

- `ExplodeList`
- `ExplodeDict`
- `ToNumeric` with `errors="coerce"`

---

## Executing results

`apply_transforms` returns an Ibis `Table` expression. The table stays lazy until you call a backend-specific execution method:

```python
# Pandas
result.execute()              # pandas.DataFrame

# Polars
result.to_polars()            # polars.DataFrame
```

You can also pass the result directly to a [sink](io.md):

```python
from red_etl.io.parquet import ParquetSink

ParquetSink("output.parquet").write(result, backend)
```

---

## Choosing a backend

| Use case | Suggested backend |
|----------|-------------------|
| Small data, familiar Pandas API | Pandas |
| Fast local analytics, typed columns | Polars |
| Large out-of-core data | DuckDB (planned) |
| Distributed big data | Spark (planned) |

---

## Next steps

- Read about [I/O adapters](io.md) to move data in and out.
- See the [validation guide](validation.md) for schema and value checks.
