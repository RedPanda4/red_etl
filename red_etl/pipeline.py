"""Pipeline helpers for applying ``RedMeta`` schemas to data."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

if TYPE_CHECKING:
    from red_etl.backends.base import Backend
    from red_etl.meta import RedMeta
    from red_etl.transforms import Transform


def apply_transforms(data: ibis.Table | object, schema: type[RedMeta], backend: Backend) -> ibis.Table:
    """Apply all transformations declared on a schema to a dataset.

    The input may be an Ibis ``Table`` expression or data in the native
    format of ``backend`` (for example a Pandas or Polars DataFrame). When
    native data is passed, it is converted to an Ibis table first.

    Columns without a ``transform`` are left unchanged. Columns with a
    ``transform`` are produced by extending the Ibis expression.

    The default execution path builds the largest possible Ibis expression
    and returns it lazily. If the backend has native overrides for some
    transforms, the pipeline is split into Ibis batches and native
    operations are applied only at those points.

    Parameters
    ----------
    data
        Ibis table expression or native dataset in the format of
        ``backend``.
    schema
        A ``RedMeta`` subclass that declares columns and transformations.
    backend
        A concrete backend that can execute native overrides and convert
        between Ibis tables and native data when needed.

    Returns
    -------
    ibis.Table
        A new Ibis table expression with all transformations applied.

    Examples
    --------
    >>> import ibis
    >>> import pandas as pd
    >>> from red_etl import RedMeta, Column
    >>> from red_etl.transforms import ConcatColumns
    >>> from red_etl.backends.pandas import PandasBackend
    >>> class User(RedMeta):
    ...     first_name = Column(str)
    ...     last_name = Column(str)
    ...     full_name = Column(str, transform=ConcatColumns([first_name, last_name], separator=" "))
    >>> df = pd.DataFrame({"first_name": ["Alice"], "last_name": ["Smith"]})
    >>> result = apply_transforms(df, User, PandasBackend())

    """
    table: ibis.Table = data if isinstance(data, ibis.Table) else backend.to_ibis_table(data)

    transforms = _collect_transforms(schema)
    native_indices = {i for i, t in enumerate(transforms) if backend.supports_native(t)}

    if not native_indices:
        return _execute_ibis_batch(transforms, table)

    result: ibis.Table = table
    ibis_batch: list[Transform] = []

    for index, transform in enumerate(transforms):
        if index in native_indices:
            if ibis_batch:
                result = _execute_ibis_batch(ibis_batch, result)
                ibis_batch = []
            native_data = backend.from_ibis_table(result)
            native_data = backend.apply_native(transform, native_data)
            result = backend.to_ibis_table(native_data)
        else:
            ibis_batch.append(transform)

    if ibis_batch:
        result = _execute_ibis_batch(ibis_batch, result)

    return result


def _collect_transforms(schema: type[RedMeta]) -> list[Transform]:
    """Collect the transforms declared on ``schema`` in column order.

    Parameters
    ----------
    schema
        A ``RedMeta`` subclass.

    Returns
    -------
    list[Transform]
        Ordered list of non-null transforms.
    """
    return [
        column.transform
        for column in schema.columns().values()
        if column.transform is not None
    ]


def _execute_ibis_batch(transforms: list[Transform], table: ibis.Table) -> ibis.Table:
    """Apply a batch of transforms as Ibis expressions.

    Parameters
    ----------
    transforms
        Transforms to apply. Each must implement ``to_ibis``.
    table
        Ibis table expression to transform.

    Returns
    -------
    ibis.Table
        The transformed Ibis table expression.
    """
    for transform in transforms:
        table = transform.to_ibis(table)
    return table
