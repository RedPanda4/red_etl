# Transforms catalog

Transforms describe how to derive or clean columns. Assign a transform to a `Column` and `apply_transforms` will apply it.

All transforms compile to Ibis expressions by default. Some operations require a backend-specific native override; the built-in backends already provide those.

---

## Importing transforms

Core transforms can be imported from `red_etl` directly:

```python
from red_etl import (
    ConcatColumns,
    ExplodeDict,
    ExplodeList,
    OutputField,
    RegexExtract,
    ToBool,
    ToDate,
    ToDateTime,
    ToNumeric,
)
```

You can also import them from `red_etl.transforms`.

---

## `ConcatColumns`

Concatenate two or more string columns with a separator.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import ConcatColumns

class User(RedMeta):
    first_name = Column(str)
    last_name = Column(str)
    full_name = Column(
        str,
        transform=ConcatColumns([first_name, last_name], separator=" "),
    )
```

| Parameter | Description |
|-----------|-------------|
| `columns` | List of `Column` descriptors or column name strings. |
| `separator` | Separator placed between values. Default `" "`. |
| `output` | Optional output column name. Inferred from the attribute name if omitted. |

---

## `ToDate`

Parse a string column to a date.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import ToDate

class Event(RedMeta):
    date_str = Column(str)
    date = Column("date", transform=ToDate(date_str, "%Y-%m-%d"))
```

| Parameter | Description |
|-----------|-------------|
| `source_column` | Source string column. |
| `format` | Date format string, e.g. `"%Y-%m-%d"`. |
| `output` | Optional output column name. |

---

## `ToDateTime`

Parse a string column to a timestamp.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import ToDateTime

class Event(RedMeta):
    ts_str = Column(str)
    ts = Column("datetime", transform=ToDateTime(ts_str, "%Y-%m-%d %H:%M:%S"))
```

| Parameter | Description |
|-----------|-------------|
| `source_column` | Source string column. |
| `format` | Timestamp format string. |
| `output` | Optional output column name. |

---

## `ToBool`

Map string or integer values to boolean.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import ToBool

class User(RedMeta):
    active_str = Column(str)
    active = Column(bool, transform=ToBool(active_str))
```

Default true values: `["1", "true", "yes"]`.  
Default false values: `["0", "false", "no"]`.  
Anything else becomes `null`.

| Parameter | Description |
|-----------|-------------|
| `source_column` | Source column. |
| `true_values` | Values mapped to `True`. |
| `false_values` | Values mapped to `False`. |
| `output` | Optional output column name. |

---

## `ToNumeric`

Cast a column to a numeric type.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import ToNumeric

class Product(RedMeta):
    price_str = Column(str)
    price = Column(float, transform=ToNumeric(price_str, "float64"))
```

| Parameter | Description |
|-----------|-------------|
| `source_column` | Source column. |
| `dtype` | Target type, e.g. `"int64"`, `"float64"`, `"int32"`, `"float32"`. |
| `errors` | `"raise"` (default) or `"coerce"`. `"coerce"` replaces invalid values with `null` and requires a backend native override. |
| `output` | Optional output column name. |

---

## `RegexExtract`

Extract a regex capture group from a string column. Returns `null` when the pattern does not match.

```python
from red_etl import Column, RedMeta
from red_etl.transforms import RegexExtract

class Log(RedMeta):
    message = Column(str)
    error_code = Column(
        str,
        transform=RegexExtract(message, r"ERROR-(\d+)", group=1),
    )
```

| Parameter | Description |
|-----------|-------------|
| `source_column` | Source string column. |
| `pattern` | Regular expression. |
| `group` | Capture group index. `0` returns the full match. |
| `output` | Optional output column name. |

---

## `ExplodeList` and `ExplodeDict`

These transforms extract multiple values from a single list or dictionary column into separate output columns. Because they produce more than one column, they are used differently from the other transforms.

See the [Explode transforms](explode-transforms.md) guide for full details.

Quick example:

```python
from red_etl import Column, OutputField, RedMeta
from red_etl.transforms import ExplodeDict, ExplodeList

class Order(RedMeta):
    items = Column("array")
    meta = Column("map")

    sku, qty = ExplodeList(
        items,
        outputs=[
            OutputField("sku", str),
            OutputField("qty", str),
        ],
    )

    country, channel = ExplodeDict(
        meta,
        outputs=[
            OutputField("country", str),
            OutputField("channel", str, source_key="ch"),
        ],
    )
```

---

## Common patterns

### Chaining transforms

A column can only have one transform, but you can produce intermediate columns to build up logic:

```python
class Order(RedMeta):
    raw_date = Column(str)
    date = Column("date", transform=ToDate(raw_date, "%Y-%m-%d"))
    year = Column(int, transform=ExtractYear(date))  # hypothetical
```

### Referencing columns from another schema

Schemas can reference columns defined on other schemas. This is common in Bronze → Silver pipelines:

```python
class BronzeOrder(RedMeta):
    order_id = Column(int)
    items = Column("array")

class SilverOrder(RedMeta):
    order_id = Column(int)
    sku, qty = ExplodeList(
        BronzeOrder.items,
        outputs=[OutputField("sku", str), OutputField("qty", str)],
    )
```

---

## Next steps

- Read the detailed [Explode transforms](explode-transforms.md) guide.
- Learn how to run transforms on different [backends](backends.md).
- Validate results with the [validation module](validation.md).
