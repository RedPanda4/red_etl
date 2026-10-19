# Red ETL — Project Specification v2

> **Package name:** `red-etl`  
> **Status:** MVP / proof-of-concept  
> **Last updated:** 2026-10-19

---

## 1. Purpose

`red-etl` is a Python framework for building **Bronze → Silver → Gold ETL pipelines** on cloud storage. It lets you declare table schemas as Python classes and apply a small, fixed catalog of cleaning transformations across multiple DataFrame engines.

The primary goal is **data cleaning**: read raw data, apply typed transformations, and write clean data back.

---

## 2. Core Design Principles

1. **Schema as code.** Tables are declared as `RedMeta` subclasses with typed `Column` attributes. This gives IDE autocompletion and refactor safety.
2. **Backend-agnostic schemas.** A `RedMeta` class does not know which engine will run it. The engine is chosen at runtime.
3. **Ibis-first execution.** Transformations are expressed as Ibis expressions and executed as a single batch when possible.
4. **Native overrides as exceptions.** Each backend can register native implementations for operations where Ibis support is weak (for example `explode`).
5. **Optional engines.** Pandas, Polars, Spark and DuckDB are optional dependencies. Each engine lives in its own module and fails gracefully if its dependency is missing.

---

## 3. Project Structure

```
red_etl/
    __init__.py            # Public core API
    column.py              # Column descriptor
    meta.py                # RedMeta base class
    transforms.py          # Transform base + concrete transforms
    pipeline.py            # apply_transforms and execution logic
    backends/              # Optional execution engines
        __init__.py
        base.py            # Backend abstract base + native override registry
        pandas.py          # PandasBackend (requires pandas)
        polars.py          # PolarsBackend (requires polars)
        duckdb.py          # (planned) DuckDBBackend
        spark.py           # (planned) SparkBackend
    io/                    # Optional I/O adapters (sources/sinks)
        __init__.py
        base.py            # Source, Sink abstract bases
        csv.py             # CSVSource, CSVSink
        parquet.py         # ParquetSource, ParquetSink
        sql.py             # SQLSource, SQLSink
        excel.py           # ExcelSource, ExcelSink (requires openpyxl)
    validation/            # Optional validation adapters
        __init__.py
        base.py            # Validator abstract base + validate_schema
        pandera/           # Pandera validators
            __init__.py    # Registry + factory (register_validator, get_validator)
            base.py        # BasePanderaValidator
            pandas.py      # PandasPanderaValidator
            polars.py      # PolarsPanderaValidator
            ibis_validator.py  # IbisPanderaValidator
            spark.py       # SparkPanderaValidator (placeholder)
tests/
    test_column.py
    test_meta.py
    test_transforms.py
    test_pipeline.py
    test_backends.py
    test_io.py
    test_validation.py
```

The core package (`red_etl`) contains only schemas, transforms and the
execution pipeline. Everything that brings an external dependency or a
separate concern — engines, file formats, databases, validation libraries —
lives in an optional addon module (`backends`, `io`, `validation`).
Addons import the core, but the core never imports an addon.

Historical brainstorming documents are kept in `archive/` (gitignored).

---

## 4. Schema Declaration

```python
from red_etl import Column, RedMeta, ConcatColumns

class User(RedMeta):
    id = Column(int, primary_key=True)
    first_name = Column(str)
    last_name = Column(str)
    full_name = Column(
        str,
        transform=ConcatColumns([first_name, last_name], separator=" "),
    )
```

- Columns are real class attributes. `User.first_name` is a `Column` object that the IDE can autocomplete.
- Transformations reference other `Column` descriptors, not magic strings.
- `RedMeta.columns()` returns the column descriptors in definition order.

---
## 5. Execution Model

### 5.1 Ibis-first batching

`apply_transforms(data, schema, backend)` receives either an Ibis ``Table``
or data in the native format of ``backend`` (for example a Pandas or Polars
DataFrame). Native data is converted to an Ibis table first. The function
builds the largest possible Ibis expression and returns a new Ibis
``Table``:

```python
import ibis
from red_etl import apply_transforms
from red_etl.backends.pandas import PandasBackend

# Either pass an Ibis table...
table = ibis.memtable(pandas_df)
result_table = apply_transforms(table, User, PandasBackend())

# ...or pass native data directly
result_table = apply_transforms(pandas_df, User, PandasBackend())
```

The result stays lazy until the sink or the user explicitly executes it.

### 5.2 Native overrides

If a backend has a native override for a transform, the pipeline splits the
Ibis plan only at that point:

```
Ibis batch 1 → native override → Ibis batch 2 → native override → Ibis batch 3
```

Native overrides materialize the current Ibis table to the backend's native
format, apply the native operation, and convert back to an Ibis table. This
keeps the common path fast while allowing backend-specific workarounds.

### 5.3 Runtime backend selection

The same schema can run on multiple engines:

```python
from red_etl.backends.pandas import PandasBackend
from red_etl.backends.polars import PolarsBackend

small = apply_transforms(ibis.memtable(pandas_df), User, PandasBackend())
large = apply_transforms(polars_table, User, PolarsBackend())
```

---

## 6. Backend Requirements

| Backend | Module | Dependency | Ibis backend used |
|---------|--------|------------|-------------------|
| Pandas | `red_etl.backends.pandas` | `pandas` | `ibis.memtable` |
| Polars | `red_etl.backends.polars` | `polars` | `ibis.polars` |
| DuckDB | `red_etl.backends.duckdb` (planned) | `duckdb` | `ibis.duckdb` |
| Spark | `red_etl.backends.spark` (planned) | `pyspark` | `ibis.pyspark` |

Importing a backend module without its dependency raises an `ImportError` with an installation hint.

---

## 7. Transformations

All transforms are implemented as Ibis expressions via `to_ibis(table)`. Backends add native overrides only when Ibis support is weak or buggy for a specific engine.

### Implemented

| Transform | Description |
|-----------|-------------|
| `ConcatColumns` | Concatenate string columns with a separator. |
| `ToDate` | Parse a string to a date using a format string. |
| `ToDateTime` | Parse a string to a timestamp using a format string. |
| `ToBool` | Map string/int values to boolean with configurable true/false sets. |
| `ToNumeric` | Cast a column to a numeric type (`int64`, `float64`, ...). `errors="raise"` or `errors="coerce"`. |
| `RegexExtract` | Extract a regex group (or the full match); returns `null` on non-match. |
| `ExplodeList` | Extract list/array elements into named output columns with strict length checking. Returns a tuple of `Column` descriptors for unpacking. |
| `ExplodeDict` | Extract dictionary values into named output columns; missing keys become `null` or raise. Returns a tuple of `Column` descriptors for unpacking. |
| `OutputField` | Factory specification used by `ExplodeList`/`ExplodeDict` to describe each produced column (`name`, `dtype`, optional `source_key`). |

### Planned

- `DateTimeToString` — date/datetime to string.
- `RegexReplace` — replace pattern.
- `FilterRows` — keep/remove rows.
- `CastType` — generic type cast.

### Explode transforms usage

`ExplodeList` and `ExplodeDict` are factory functions that return a tuple of
`Column` descriptors. This keeps the declaration concise and ensures the source
list or dictionary is processed only once.

```python
from red_etl import Column, OutputField, RedMeta
from red_etl.transforms import ExplodeDict, ExplodeList

class Order(RedMeta):
    raw_items = Column("array")
    raw_meta = Column("map")

    sku, qty = ExplodeList(
        raw_items,
        outputs=[
            OutputField("sku", str),
            OutputField("qty", str),
        ],
    )

    country, channel = ExplodeDict(
        raw_meta,
        outputs=[
            OutputField("country", str),
            OutputField("channel", str, source_key="ch"),
        ],
    )
```

- Each output name and type is declared exactly once.
- Use `source_key` when the dictionary key differs from the desired column name.
- A single-output explode must use a trailing comma to unpack the tuple:
  `col_a, = ExplodeDict(raw, outputs=[OutputField("col_a", int)])`.

### Design note: `OutputField` is not a `Column`

`OutputField` and `Column` share `name` and `dtype`, but they are intentionally
not in the same inheritance hierarchy:

- `Column` is a **descriptor** that lives on a `RedMeta` class and owns optional
  transformation logic.
- `OutputField` is a **factory argument** consumed by `ExplodeList`/`ExplodeDict`
  to produce multiple `Column` descriptors at once.

If future needs (for example common validation or serialization) justify a shared
base class, the shared fields can be extracted into a small `FieldSpec` protocol
without changing public APIs.

### Null semantics

Different backends represent missing values differently (Pandas uses `NaN` / `NaT`,
Polars uses `null`). The semantic meaning is the same: the value is missing.
Transforms normalize edge cases where possible; for example `RegexExtract` returns
`null` on a non-match on every backend.

---

## 8. I/O Layer

Reading and writing are separate from transformation. They live in `red_etl.io`.

```
red_etl/io/
    base.py       # Source, Sink abstract bases
    csv.py        # CSVSource, CSVSink
    parquet.py    # ParquetSource, ParquetSink
    sql.py        # SQLSource, SQLSink
    excel.py      # ExcelSource, ExcelSink
```

Sources return an **Ibis ``Table`` expression**. Sinks accept an Ibis
``Table`` expression. Each source/sink delegates the actual read/write to the
chosen backend so that the table is backed by the engine you intend to use
(Pandas, Polars, DuckDB, Spark, etc.).

Sources expose format-specific parameters:

| Format | Parameters |
|--------|------------|
| CSV | `separator`, `encoding`, `header`, `na_values`, `dtype` |
| Parquet | `columns` |
| SQL | `query` or `schema` + `table_name` |
| Excel | `sheet_name`, `header` |

## 9. Pipeline Layers (Medallion)

```
Bronze (csv / json / parquet / database)
    ↓ Source.read(backend) → ibis.Table
RedMeta schema + backend
    ↓ apply_transforms(table, schema, backend) → ibis.Table
Silver
    ↓ apply_transforms (table, schema, backend) → ibis.Table
Gold
    ↓ Sink.write(table, backend)
```

- Data stays as an Ibis expression as long as possible.
- Native overrides only materialize when an operation cannot be expressed in Ibis.
- A `Pipeline` class that ties Source → transforms → Sink is planned but not
  yet implemented.

---

## 10. Validation

Validation is an **optional addon**, not part of the core framework. It lives
in `red_etl.validation` and is imported only when needed, following the same
addon pattern as `red_etl.io`.

There are two layers:

1. **Schema validation** (`validate_schema`) — lightweight check of column
   names and types against an Ibis ``Table`` expression. It never executes the
   table or pulls rows into memory, so it is safe for large datasets on any
   backend.

   ```python
   from red_etl.validation import validate_schema

   validate_schema(table, User)
   ```

2. **Full value validation** (`validate`) — backend-aware Pandera validation.
   When a :class:`Backend` is supplied, the validator uses the Pandera module
   that matches the backend's native format (``pandera.pandas``,
   ``pandera.polars``, ...). This avoids converting a Spark or Polars dataset
   to Pandas just for validation.

   ```python
   from red_etl.validation import validate
   from red_etl.backends.polars import PolarsBackend

   validate(df, User, backend=PolarsBackend())
   ```

Implemented design:

- `red_etl.validation.base.Validator` is an abstract base.
- `red_etl.validation.base.validate_schema()` performs a lightweight,
  execution-free check of column names and types on an Ibis ``Table``.
- `red_etl.validation.base` exposes a generic validator registry:
  - `register_validator(name, validator_cls)` accepts any ``Validator``
    subclass, not just Pandera-based ones.
  - `get_validator(backend)` returns the registered validator instance.
- `red_etl.validation.pandera` provides the package-default validators
  (`PandasPanderaValidator`, `PolarsPanderaValidator`, ...) and registers
  them for their respective backends. Users can override these defaults or
  register non-Pandera validators through the same registry.
- `red_etl.validation.pandera.base.BasePanderaValidator` is a generic base for
  Pandera validators. Concrete subclasses live in backend-specific modules
  (`pandas.py`, `polars.py`, `ibis_validator.py`, `spark.py`).
- The core `RedMeta` and `Column` classes do not depend on validation. The
  addon reads the schema through the existing introspection API
  (`columns()`, `dtype`, `nullable`, `primary_key`).
- For now validation is **strict**: the input must contain exactly the
  columns declared on the schema, with matching names and types. Handling of
  missing or extra columns is left as a future improvement.
- If a backend does not have a registered validator, `get_validator()` raises
  `NotImplementedError` with a clear message. The caller can fall back to
  `validate_schema()` for a memory-safe schema check.
- Validation checkpoints can be attached to pipeline steps (input,
  intermediate, output) once the `Pipeline` class is implemented.
- Validation is optional and configurable per step.

No core changes were required to support validation as an addon.

---

## 11. Metadata Persistence

`red_elt_save` (planned) will persist metadata definitions to SQL or files so that schemas can be loaded at runtime instead of only living in code. It is an optional, isolated module.

---

## 12. Developer Rules

1. **Docstrings are mandatory** for every module, class, method and function.
2. **Unit tests are mandatory** for every source file and public function/method.
3. Keep the core independent of optional engines.
4. Prefer Ibis expressions; add native overrides only for proven edge cases.
5. Keep the API small and explicit.

---

## 13. Roadmap

1. ~~Add remaining core transforms~~ (done).
2. Normalize remaining backend-specific edge cases across DuckDB/Polars/Spark.
3. Add `DuckDBBackend` for fast local analytical execution.
4. ~~Add source/sink abstraction~~ (done for local files; add S3 path support).
5. Add a `Pipeline` class that wires Source → transforms → Sink.
6. ~~Add `red_etl.validation` addon with Pandera schema generation and validation checkpoints~~ (basic implementation done).
7. Make validation column-matching configurable (allow missing/extra columns).
8. Make validation per column
9. Add `red_elt_save` metadata persistence module.
10. Add `SparkBackend` for large-scale pipelines.

---

*This document is the living project spec. Older brainstorming notes live in `archive/` (gitignored).*
