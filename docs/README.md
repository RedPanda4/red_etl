# Red ETL Documentation

Welcome to the `red-etl` documentation. These pages are written for **users** of the library — people who want to declare schemas, run transformations, and move data between sources and sinks.

If you want to extend `red-etl` itself (add a new transform, backend, validator, or I/O adapter), see the guides in [`extending/README.md`](extending/README.md).

---

## What is red-etl?

`red-etl` is a small Python framework for **Bronze → Silver → Gold ETL pipelines**. You declare table schemas as Python classes and apply a fixed catalog of cleaning transformations across multiple DataFrame engines.

Key ideas:

- **Schema as code** — tables are `RedMeta` subclasses with typed `Column` attributes.
- **Backend-agnostic** — the same schema runs on Pandas, Polars, or future backends.
- **Ibis-first** — transformations compile to Ibis expressions and run as one batch when possible.
- **Optional engines** — install only the backends you need.

---

## Getting started

| Document | What it covers |
|----------|----------------|
| [Quick start](quickstart.md) | Install `red-etl`, declare your first schema, and run a transformation. |
| [Schemas](schemas.md) | How `RedMeta` and `Column` work. |

## Using transforms

| Document | What it covers |
|----------|----------------|
| [Transforms catalog](transforms.md) | All built-in transforms with examples for each one. |
| [Explode transforms](explode-transforms.md) | Detailed guide for `ExplodeList` and `ExplodeDict`. |

## Reading and writing data

| Document | What it covers |
|----------|----------------|
| [Backends](backends.md) | Supported execution engines and how to pick one. |
| [I/O adapters](io.md) | Sources and sinks for CSV, Parquet, SQL, and Excel. |
| [Pipelines](pipelines.md) | Bronze → Silver → Gold pipeline concepts. |

## Validation

| Document | What it covers |
|----------|----------------|
| [Validation](validation.md) | Schema checks and full value validation with Pandera. |

## Extending red-etl

These guides are for contributors or advanced users who need to extend the framework:

| Document | What it covers |
|----------|----------------|
| [Extending overview](extending/README.md) | Where each extension type lives and how to register it. |
| [Adding a transform](extending/adding-transforms.md) | Add a new backend-agnostic transform. |
| [Adding a backend native override](extending/adding-native-overrides.md) | Override a transform with backend-specific code. |
| [Adding a validator](extending/adding-validators.md) | Add a new schema/value validator. |
| [Adding an I/O adapter](extending/adding-io.md) | Add a new source or sink. |

---

## Quick links

- Living project spec: [`PROJECT.md`](../PROJECT.md)
- Source code: [`red_etl/`](../red_etl/)
- Examples: [`examples/`](../examples/)
- Tests: [`tests/`](../tests/)
