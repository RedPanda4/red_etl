# Red ETL Documentation

This folder contains guides and reference material for `red-etl`.

## Available guides

| Document | What it covers |
|----------|----------------|
| [Adding Native Transforms](ADDING_NATIVE_TRANSFORMS.md) | How to add a backend-specific native override for a transform. Includes a complete Pandas example for `ConcatColumns`. |

## I/O adapters

Sources and sinks live in `red_etl.io` and are kept separate from the core.

| Format | Source | Sink | Extra dependencies |
|--------|--------|------|--------------------|
| CSV | `CSVSource` | `CSVSink` | `pandas` |
| Parquet | `ParquetSource` | `ParquetSink` | `pandas` |
| SQL | `SQLSource` | `SQLSink` | `pandas`, `sqlalchemy` |
| Excel | `ExcelSource` | `ExcelSink` | `pandas`, `openpyxl` |

## Planned documents

- `TRANSFORMS.md` — catalog of available transforms and how to use each one.
- `BACKENDS.md` — list of supported backends, their dependencies, and how to add a new one.
- `IO.md` — detailed guide for sources and sinks (parameters, S3, partitions).
- `PIPELINES.md` — how to build Bronze → Silver → Gold pipelines with sources and sinks.
- `VALIDATION.md` — integrating Pandera for schema validation.
- `ARCHITECTURE.md` — deep dive into the core design (RedMeta, Column, Transform, Backend, Pipeline).

## Quick links

- Living project spec: [`PROJECT.md`](../PROJECT.md)
- Current code: [`red_etl/`](../red_etl/)
- Tests: [`tests/`](../tests/)
