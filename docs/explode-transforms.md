# Explode transforms

`ExplodeList` and `ExplodeDict` extract multiple values from a single list or dictionary column into named output columns. They are useful when raw data contains nested structures that you want to flatten into a clean tabular shape.

---

## `ExplodeList`

Extract list/array elements into named columns by position.

```python
from red_etl import Column, OutputField, RedMeta
from red_etl.transforms import ExplodeList

class Order(RedMeta):
    items = Column("array")  # ["SKU-1", "2", "SKU-2", "1"]

    sku_1, qty_1, sku_2, qty_2 = ExplodeList(
        items,
        outputs=[
            OutputField("sku_1", str),
            OutputField("qty_1", str),
            OutputField("sku_2", str),
            OutputField("qty_2", str),
        ],
    )
```

The number of `OutputField` entries must match the length of every list in the source column. Lists with a different length raise `ValueError`. Missing values inside the list become `null`.

### `OutputField`

```python
OutputField(name, dtype, source_key=None)
```

| Parameter | Description |
|-----------|-------------|
| `name` | Name of the output column. |
| `dtype` | Logical data type of the output column. |
| `source_key` | Only used by `ExplodeDict`. |

### Single-output explode

If you only need one element, use a trailing comma to unpack the tuple:

```python
first_item, = ExplodeList(
    items,
    outputs=[OutputField("first_item", str)],
)
```

---

## `ExplodeDict`

Extract dictionary/map values into named columns by key.

```python
from red_etl import Column, OutputField, RedMeta
from red_etl.transforms import ExplodeDict

class Order(RedMeta):
    meta = Column("map")  # {"country": "PT", "channel": "web"}

    country, channel = ExplodeDict(
        meta,
        outputs=[
            OutputField("country", str),
            OutputField("channel", str, source_key="ch"),
        ],
    )
```

| Parameter | Description |
|-----------|-------------|
| `source_column` | Source dictionary column. |
| `outputs` | List of `OutputField` descriptors. |
| `on_missing` | `"null"` (default) inserts `null` for missing keys; `"raise"` raises `KeyError`. |

Use `source_key` when the dictionary key differs from the desired column name.

### Missing keys

With `on_missing="null"` (the default), keys that are not present in a dictionary become `null`:

```python
{"country": "US"}  # channel -> null
```

With `on_missing="raise"`, the same row raises `KeyError`.

---

## Combining both transforms

A typical Bronze → Silver pipeline explodes a list and a dictionary in the same schema:

```python
class BronzeOrder(RedMeta):
    order_id = Column(int)
    items = Column("array")
    meta = Column("map")


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
```

A runnable version of this example is in [`examples/explode_usage.py`](../examples/explode_usage.py).

---

## Notes

- `ExplodeList` and `ExplodeDict` are factory functions, not `Transform` subclasses. They return a tuple of `Column` descriptors.
- The actual transform is attached to the first returned column; the remaining columns reuse the same transform result.
- Both transforms require a backend-specific native override. The built-in Pandas and Polars backends provide them.

---

## Next steps

- Back to the [transforms catalog](transforms.md).
- Learn about [backends](backends.md) and [I/O adapters](io.md).
