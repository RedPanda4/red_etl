# Extending red-etl

This folder contains guides for extending `red-etl` itself. Most users do not need these pages; they are aimed at contributors or advanced users who need a capability that is not built in.

---

## What you can extend

| Guide | What it covers |
|-------|----------------|
| [Adding a transform](adding-transforms.md) | Add a new backend-agnostic transform in `red_etl/transforms.py`. |
| [Adding a backend native override](adding-native-overrides.md) | Override a transform with backend-specific code. |
| [Adding a validator](adding-validators.md) | Add a new schema/value validator in `red_etl/validation/`. |
| [Adding an I/O adapter](adding-io.md) | Add a new source or sink in `red_etl/io/`. |

---

## Design principles

When extending the framework, keep these rules in mind:

1. **Core stays small and dependency-free.** New transforms belong in the core, but engines, file formats, databases, and validation libraries are optional addons.
2. **Implement transforms as Ibis expressions first.** Only add backend native overrides when Ibis support is missing, buggy, or significantly slower.
3. **Addons import the core; the core never imports an addon.** `red_etl.transforms` must not import `red_etl.backends` or `red_etl.io`.
4. **Backends are optional.** A backend module must fail gracefully with a clear installation hint when its dependency is missing.
5. **Docstrings and tests are mandatory.** Every public module, class, method, and function needs a docstring; every source file needs unit tests.

---

## Quick links

- Core transforms: [`red_etl/transforms.py`](../../red_etl/transforms.py)
- Backends: [`red_etl/backends/`](../../red_etl/backends/)
- I/O adapters: [`red_etl/io/`](../../red_etl/io/)
- Validation: [`red_etl/validation/`](../../red_etl/validation/)
- Tests: [`tests/`](../../tests/)
