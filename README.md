# red-etl

Metadata-first, backend-agnostic data cleaning for Bronze → Silver → Gold ETL pipelines.

`red-etl` lets you declare table schemas as Python classes and apply a fixed catalog of
cleaning transformations across multiple DataFrame engines. The same schema runs on
Pandas, Polars, or future backends with minimal changes.

```python
from red_etl import Column, OutputField, RedMeta, apply_transforms
from red_etl.backends.polars import PolarsBackend
from red_etl.transforms import ExplodeDict, ExplodeList


class BronzeOrder(RedMeta):
    order_id = Column(int)
    items = Column("array")    # ["SKU-1", "2", "SKU-2", "1"]
    meta = Column("map")       # {"country": "PT", "channel": "web"}


class SilverOrder(RedMeta):
    order_id = Column(int)

    sku_1, qty_1, sku_2, qty_2 = ExplodeList(
        BronzeOrder.items,
        outputs=[
            OutputField("sku_1", str),
            OutputField("qty_1", str),
            OutputField("sku_2", str),
            OutputField("qty_2", str),
        ],
    )

    country, channel = ExplodeDict(
        BronzeOrder.meta,
        outputs=[
            OutputField("country", str),
            OutputField("channel", str),
        ],
    )


result = apply_transforms(bronze_df, SilverOrder, PolarsBackend())
```

## Highlights

- **Schema as code** — `RedMeta` classes with typed `Column` descriptors give you IDE
  autocompletion and refactor safety.
- **Backend-agnostic** — the same schema runs on Pandas, Polars, DuckDB (planned), or
  Spark (planned). Pick the engine at runtime.
- **Ibis-first execution** — transformations are compiled to Ibis expressions and run
  as a single batch when possible.
- **Native overrides as exceptions** — backends can provide native implementations for
  operations where Ibis support is weak or inconsistent.
- **Optional engines** — install only what you need.

## Installation

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

## Quick start

```python
import pandas as pd
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


df = pd.DataFrame({
    "first_name": ["Alice", "Bob"],
    "last_name": ["Smith", "Jones"],
})

result = apply_transforms(df, User, PandasBackend())
print(result.execute()["full_name"].tolist())
# ['Alice Smith', 'Bob Jones']
```

## Supported transforms

| Transform | Description |
|-----------|-------------|
| `ConcatColumns` | Concatenate string columns with a separator. |
| `ToDate` / `ToDateTime` | Parse strings to dates/timestamps. |
| `ToBool` | Map string/int values to boolean. |
| `ToNumeric` | Cast to numeric with `raise` or `coerce` error handling. |
| `RegexExtract` | Extract a regex group; returns `null` on non-match. |
| `ExplodeList` | Extract list/array elements into named columns. |
| `ExplodeDict` | Extract dictionary values into named columns. |

See [`PROJECT.md`](PROJECT.md) for the full specification and [`docs/`](docs/) for
additional guides.

## Backends

| Backend | Module | Dependency |
|---------|--------|------------|
| Pandas | `red_etl.backends.pandas` | `pandas` |
| Polars | `red_etl.backends.polars` | `polars` |
| DuckDB | `red_etl.backends.duckdb` | planned |
| Spark  | `red_etl.backends.spark`  | planned |

## I/O layer

Sources and sinks live in `red_etl.io` and are separate from transformations:

| Format | Source | Sink |
|--------|--------|------|
| CSV | `CSVSource` | `CSVSink` |
| Parquet | `ParquetSource` | `ParquetSink` |
| SQL | `SQLSource` | `SQLSink` |
| Excel | `ExcelSource` | `ExcelSink` |

## Development

```bash
# Install in editable mode with all optional dependencies
pip install -e ".[pandas,polars,dev]"

# Run the test suite
pytest tests/

# Run the explode example
PYTHONPATH=. python examples/explode_usage.py
```

## Project status

MVP / proof-of-concept. Core transforms, Pandas and Polars backends, and the I/O
abstraction are implemented. A `Pipeline` class that wires Source → transforms → Sink
and Pandera validation hooks are on the roadmap.

See [`PROJECT.md`](PROJECT.md) for the living specification.

## License

MIT
