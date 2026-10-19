# Pipelines

A `red-etl` pipeline moves data through the classic Bronze → Silver → Gold medallion architecture:

```
Bronze (raw)
    ↓ Source.read(backend) → ibis.Table
RedMeta schema + backend
    ↓ apply_transforms(table, schema, backend) → ibis.Table
Silver (cleaned)
    ↓ apply_transforms(table, schema, backend) → ibis.Table
Gold (aggregated / ready)
    ↓ Sink.write(table, backend)
```

Data stays as a lazy Ibis expression as long as possible. Native backend operations only materialize when a transform requires it.

---

## Bronze → Silver example

```python
from red_etl import Column, RedMeta, apply_transforms
from red_etl.backends.pandas import PandasBackend
from red_etl.io.csv import CSVSource, CSVSink
from red_etl.transforms import ToDate, ToNumeric


class BronzeOrder(RedMeta):
    order_id = Column(str)
    order_date = Column(str)
    amount = Column(str)


class SilverOrder(RedMeta):
    order_id = Column(int, transform=ToNumeric(BronzeOrder.order_id, "int64"))
    order_date = Column("date", transform=ToDate(BronzeOrder.order_date, "%Y-%m-%d"))
    amount = Column(float, transform=ToNumeric(BronzeOrder.amount, "float64"))


backend = PandasBackend()

source = CSVSource("bronze_orders.csv")
bronze = source.read(backend)

silver = apply_transforms(bronze, SilverOrder, backend)

sink = CSVSink("silver_orders.csv")
sink.write(silver, backend)
```

---

## Silver → Gold example

```python
class GoldSummary(RedMeta):
    order_date = Column("date")
    total_amount = Column(float)


# Aggregate the silver table with Ibis
gold = (
    silver
    .group_by("order_date")
    .agg(total_amount=silver["amount"].sum())
)

ParquetSink("gold_summary.parquet").write(gold, backend)
```

---

## Design notes

- `Source.read` returns an Ibis `Table`.
- `apply_transforms` returns an Ibis `Table`.
- `Sink.write` accepts an Ibis `Table`.
- A planned `Pipeline` class will wire these steps together and support configurable validation checkpoints.

---

## Next steps

- See the [I/O adapters](io.md) reference for all source/sink options.
- Add [validation](validation.md) at each pipeline step.
- Run the full example in [`examples/explode_usage.py`](../examples/explode_usage.py).
