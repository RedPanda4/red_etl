# Adding a validator

This guide shows how to add a new validator to `red_etl.validation`. Validators turn a `RedMeta` schema into a backend-specific validation object and run it against a dataset.

`red-etl` ships with Pandera-based validators as the default, but the registry in `red_etl.validation.base` is generic and accepts any `Validator` subclass.

---

## The `Validator` base class

A validator must implement two methods:

```python
from abc import ABC, abstractmethod
from red_etl.meta import RedMeta

class Validator(ABC):
    @abstractmethod
    def from_schema(self, schema: type[RedMeta]) -> Any:
        """Build the validator from a RedMeta schema."""

    @abstractmethod
    def validate(self, data: Any) -> Any:
        """Validate data and return the validated result."""
```

`from_schema` is called once to build the backend-specific validation object. `validate` is called with the dataset and returns the validated result.

---

## Example: custom Pandas validator

Here is a tiny custom validator that checks for non-negative integers in Pandas:

```python
import pandas as pd

from red_etl.meta import RedMeta
from red_etl.validation.base import Validator, register_validator


class NonNegativePandasValidator(Validator):
    """Example validator that rejects negative integers."""

    def __init__(self) -> None:
        self._schema: type[RedMeta] | None = None

    def from_schema(self, schema: type[RedMeta]) -> pd.DataFrame:
        self._schema = schema
        return pd.DataFrame()

    def validate(self, data: pd.DataFrame) -> pd.DataFrame:
        if self._schema is None:
            raise RuntimeError("from_schema must be called before validate")

        for name, column in self._schema.columns().items():
            if column.dtype is int and name in data.columns:
                if (data[name] < 0).any():
                    raise ValueError(f"Column {name!r} contains negative values")
        return data
```

---

## Register the validator

Register the validator for a backend name so `get_validator` and `validate(..., backend=...)` can find it:

```python
register_validator("pandas", NonNegativePandasValidator)
```

You can also use `register_validator` as a decorator:

```python
@register_validator("pandas")
class NonNegativePandasValidator(Validator):
    ...
```

---

## Use the validator

Once registered, the validator is picked automatically by `validate`:

```python
from red_etl.validation import validate
from red_etl.backends.pandas import PandasBackend

validate(df, MySchema, backend=PandasBackend())
```

Or pass it explicitly:

```python
from red_etl.validation import validate

validate(df, MySchema, validator=NonNegativePandasValidator())
```

---

## Replacing the default Pandera validator

Registering a validator for an existing backend name replaces the previous entry. This lets you override the default Pandera validator for Pandas or Polars:

```python
from red_etl.validation.base import register_validator

register_validator("pandas", MyCustomValidator)
```

---

## Pandera-based validators

If you want to stay within the Pandera ecosystem, subclass `BasePanderaValidator` from `red_etl.validation.pandera.base` and implement the backend-specific conversion. Look at the existing implementations for reference:

- `red_etl/validation/pandera/pandas.py`
- `red_etl/validation/pandera/polars.py`
- `red_etl/validation/pandera/ibis_validator.py`

---

## Summary

1. Subclass `Validator` (or `BasePanderaValidator`).
2. Implement `from_schema` and `validate`.
3. Register the class with `register_validator("backend_name", MyValidator)`.
4. Add unit tests in `tests/test_validation.py`.
