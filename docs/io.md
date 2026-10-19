# I/O adapters

`red-etl` separates reading and writing from transformation. Sources read data into an Ibis `Table` expression; sinks write an Ibis `Table` expression to a destination.

All I/O adapters live in `red_etl.io`.

---

## Quick example

```python
from red_etl.io.csv import CSVSource, CSVSink
from red_etl.backends.pandas import PandasBackend
from red_etl import apply_transforms

backend = PandasBackend()

# Read
source = CSVSource("input.csv", separator=";")
table = source.read(backend)

# Transform
result = apply_transforms(table, User, backend)

# Write
sink = CSVSink("output.csv", separator=";")
sink.write(result, backend)
```

---

## Sources and sinks

| Format | Source | Sink | Extra dependencies |
|--------|--------|------|--------------------|
| CSV | `CSVSource` | `CSVSink` | `pandas` (Polars optional) |
| Parquet | `ParquetSource` | `ParquetSink` | `pandas` (Polars optional) |
| SQL | `SQLSource` | `SQLSink` | `pandas`, `sqlalchemy` |
| Excel | `ExcelSource` | `ExcelSink` | `pandas`, `openpyxl` |

Import from the format-specific module:

```python
from red_etl.io.csv import CSVSource, CSVSink
from red_etl.io.parquet import ParquetSource, ParquetSink
from red_etl.io.sql import SQLSource, SQLSink
from red_etl.io.excel import ExcelSource, ExcelSink
```

---

## CSV

```python
from red_etl.io.csv import CSVSource, CSVSink

source = CSVSource(
    "data.csv",
    separator=",",
    encoding="utf-8",
    header=True,
)
table = source.read(backend)

sink = CSVSink(
    "output.csv",
    separator=",",
    encoding="utf-8",
    header=True,
    index=False,  # Pandas only
)
sink.write(table, backend)
```

Additional reader/writer options are forwarded to the backend.

---

## Parquet

```python
from red_etl.io.parquet import ParquetSource, ParquetSink

source = ParquetSource("data.parquet", columns=["a", "b"])
table = source.read(backend)

sink = ParquetSink("output.parquet", compression="snappy")
sink.write(table, backend)
```

---

## SQL

```python
from red_etl.io.sql import SQLSource, SQLSink

# Read a full table
source = SQLSource("sqlite:///data.db", table_name="users")
table = source.read(backend)

# Read a query
source = SQLSource(
    "sqlite:///data.db",
    query="SELECT id, name FROM users WHERE active = 1",
)
table = source.read(backend)

# Write a table
sink = SQLSink(
    "sqlite:///data.db",
    table_name="users_clean",
    if_exists="replace",  # "fail", "replace", or "append"
)
sink.write(table, backend)
```

---

## Excel

```python
from red_etl.io.excel import ExcelSource, ExcelSink

source = ExcelSource("data.xlsx", sheet_name="Users", header=0)
table = source.read(PandasBackend())

sink = ExcelSink("output.xlsx", sheet_name="Users", index=False)
sink.write(table, PandasBackend())
```

Excel I/O currently requires `PandasBackend`.

---

## Backend delegation

Sources and sinks delegate the actual read/write to the backend you supply. This means a CSV read with `PolarsBackend()` returns an Ibis table backed by Polars, while the same source with `PandasBackend()` returns a table backed by Pandas.

If a source or sink does not support the supplied backend, it raises `NotImplementedError`.

---

## Next steps

- Put sources, transforms, and sinks together in [Pipelines](pipelines.md).
- Validate data with [Validation](validation.md).
