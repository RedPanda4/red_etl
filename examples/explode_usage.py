"""Example: using ExplodeList and ExplodeDict together.

This example shows a Bronze → Silver transformation where the raw input
contains a list column and a dictionary column. The Silver schema explodes
both into typed, named columns.

Polars is used for the main example because it natively supports typed
list and struct columns.
"""

from __future__ import annotations

import polars as pl

from red_etl import Column, OutputField, RedMeta, apply_transforms
from red_etl.backends.polars import PolarsBackend
from red_etl.transforms import ExplodeDict, ExplodeList


class BronzeOrder(RedMeta):
    """Raw order data as it arrives from the source.

    - ``items`` is a list of product codes and quantities in pairs.
    - ``meta`` is a struct/dictionary with extra attributes.
    """

    order_id = Column(int)
    items = Column("array")  # ["SKU-1", 2, "SKU-2", 1]
    meta = Column("map")  # {"country": "PT", "channel": "web"}


class SilverOrder(RedMeta):
    """Cleaned order data with list and dict elements extracted into columns."""

    order_id = Column(int)

    # items has 4 positions: [sku_1, qty_1, sku_2, qty_2]
    sku_1, qty_1, sku_2, qty_2 = ExplodeList(
        BronzeOrder.items,
        outputs=[
            OutputField("sku_1", str),
            OutputField("qty_1", str),
            OutputField("sku_2", str),
            OutputField("qty_2", str),
        ],
    )

    # meta keys mapped to output columns
    country, channel = ExplodeDict(
        BronzeOrder.meta,
        outputs=[
            OutputField("country", str),
            OutputField("channel", str),
        ],
    )


if __name__ == "__main__":
    # The list column must have a uniform element type.
    # Here all items are strings; in a real pipeline you might use ToNumeric
    # to cast the quantity columns afterwards.
    bronze_df = pl.DataFrame(
        {
            "order_id": [1, 2, 3],
            "items": [
                ["SKU-1", "2", "SKU-2", "1"],
                ["SKU-3", "5", None, None],  # missing second product -> nulls
                ["SKU-4", "1"],  # only one product -> will raise
            ],
            "meta": [
                {"country": "PT", "channel": "web"},
                {"country": "BR", "channel": "mobile"},
                {"country": "US"},  # missing channel -> null
            ],
        }
    )

    print("Bronze:")
    print(bronze_df)
    print()

    # Transform order 1 and 2 only, because order 3 has the wrong list length.
    valid_df = bronze_df[:2]
    result = apply_transforms(valid_df, SilverOrder, PolarsBackend())

    print("Silver:")
    print(result.to_polars())
    print()

    # Demonstrate strict list length failure.
    print("Trying to explode a list with wrong length:")
    try:
        apply_transforms(bronze_df[2:], SilverOrder, PolarsBackend())
    except ValueError as exc:
        print(f"ValueError: {exc}")
