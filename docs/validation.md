# Validation

`red-etl` provides two validation layers. Both are optional and live in `red_etl.validation`.

---

## Schema validation

`validate_schema` checks that an Ibis `Table` has exactly the columns and types declared on a `RedMeta` schema. It does **not** execute the table or pull rows into memory, so it is safe for large datasets.

```python
from red_etl.validation import validate_schema

result = apply_transforms(df, User, backend)
validate_schema(result, User)
```

The check is strict:

- Column names must match exactly.
- Column types must match the schema.

Missing or extra columns raise `ValueError`.

---

## Full value validation

`validate` runs a backend-aware validator that checks actual values. By default it uses Pandera and selects the validator that matches your backend's native format (Pandas, Polars, Ibis, etc.). This avoids converting large datasets to Pandas just for validation.

```python
from red_etl.validation import validate
from red_etl.backends.polars import PolarsBackend

validate(df, User, backend=PolarsBackend())
```

You can also validate an Ibis table directly:

```python
result = apply_transforms(df, User, backend)
validate(result, User)
```

If no backend is supplied, `validate` infers one from the data type.

### Optional dependency

Value validation requires Pandera:

```bash
pip install "red-etl[validation]"
```

---

## Registered validators

The built-in Pandera validators are registered for the following backends:

| Backend | Validator |
|---------|-----------|
| pandas | `PandasPanderaValidator` |
| polars | `PolarsPanderaValidator` |
| ibis   | `IbisPanderaValidator` |

If a backend has no registered validator, `validate` raises `NotImplementedError` and suggests using `validate_schema` instead.

---

## Validation in pipelines

A common pattern is to validate at pipeline boundaries:

```python
from red_etl.validation import validate_schema

# Validate raw input
validate_schema(raw_table, BronzeSchema)

# Transform
silver = apply_transforms(raw_table, SilverSchema, backend)

# Validate output
validate_schema(silver, SilverSchema)
validate(silver, SilverSchema, backend=backend)
```

When the planned `Pipeline` class is added, validation checkpoints will be configurable per step.

---

## Next steps

- Read about [pipelines](pipelines.md) to wire sources, transforms, and sinks together.
- See [Adding a validator](extending/adding-validators.md) if you need a custom validator.
