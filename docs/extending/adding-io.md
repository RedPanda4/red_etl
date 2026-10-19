# Adding an I/O adapter

This guide shows how to add a new source or sink to `red_etl.io`. Sources read data into an Ibis `Table` expression; sinks write an Ibis `Table` expression to a destination.

---

## Base classes

All sources and sinks inherit from the abstract bases in `red_etl.io.base`:

```python
from abc import abstractmethod
from red_etl.backends.base import Backend

class Source(ABC):
    @abstractmethod
    def read(self, backend: Backend) -> ibis.Table:
        """Read data and return it in the native format of backend."""

class Sink(ABC):
    @abstractmethod
    def write(self, data: Any, backend: Backend) -> None:
        """Write data to the sink using the supplied backend's format."""
```

Sources return an Ibis `Table`. Sinks accept an Ibis `Table`.

---

## Example: JSON source and sink

Below is a minimal example of a JSON source and sink backed by Pandas.

### Source

```python
from __future__ import annotations

import ibis
from pathlib import Path
from typing import Any

from red_etl.io.base import Source
from red_etl.backends.base import Backend
from red_etl.backends.pandas import PandasBackend


try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "JSON I/O requires pandas. Install it with: pip install 'red-etl[pandas]'"
    ) from exc


class JSONSource(Source):
    """Read a JSON file into an Ibis Table expression."""

    def __init__(self, path: str | Path, **kwargs: Any) -> None:
        self.path = str(path)
        self.kwargs = kwargs

    def read(self, backend: Backend) -> ibis.Table:
        if not isinstance(backend, PandasBackend):
            raise NotImplementedError("JSONSource only supports PandasBackend")
        df = pd.read_json(self.path, **self.kwargs)
        return ibis.memtable(df)
```

### Sink

```python
from pathlib import Path
from typing import Any

from red_etl.io.base import Sink
from red_etl.backends.base import Backend
from red_etl.backends.pandas import PandasBackend


class JSONSink(Sink):
    """Write an Ibis Table expression to a JSON file."""

    def __init__(self, path: str | Path, **kwargs: Any) -> None:
        self.path = str(path)
        self.kwargs = kwargs

    def write(self, table: ibis.Table, backend: Backend) -> None:
        if not isinstance(backend, PandasBackend):
            raise NotImplementedError("JSONSink only supports PandasBackend")
        df = backend.from_ibis_table(table)
        df.to_json(self.path, **self.kwargs)
```

---

## Delegating to the backend

When possible, delegate the actual read/write to the backend so that the resulting table is backed by the engine the user chose. For example, `CSVSource` calls `backend.read_csv(...)` instead of reading directly with Pandas. This lets the same source work with both `PandasBackend` and `PolarsBackend`.

If the backend base class does not define a method for your format, add the method to `Backend` in `red_etl/backends/base.py` and implement it for each backend.

---

## Export the adapter

If the adapter is public, export it from `red_etl/io/__init__.py`:

```python
from red_etl.io.json import JSONSource, JSONSink

__all__ = [
    # ... existing entries
    "JSONSource",
    "JSONSink",
]
```

---

## Test the adapter

Add tests in `tests/test_io.py`:

```python
import json
from red_etl.io.json import JSONSource, JSONSink
from red_etl.backends.pandas import PandasBackend


def test_json_source_sink_round_trip(tmp_path) -> None:
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"a": [1, 2], "b": ["x", "y"]}))

    backend = PandasBackend()
    table = JSONSource(path).read(backend)
    JSONSink(path).write(table, backend)

    df = JSONSource(path).read(backend).execute()
    assert df["a"].tolist() == [1, 2]
```

---

## Optional dependencies

I/O adapters must fail gracefully when their dependency is missing:

```python
try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "JSON I/O requires pandas. Install it with: pip install 'red-etl[pandas]'"
    ) from exc
```

---

## Summary

1. Create a module under `red_etl/io/` for the new format.
2. Implement `Source.read(backend)` and/or `Sink.write(table, backend)`.
3. Delegate to the backend when possible; raise `NotImplementedError` for unsupported backends.
4. Export the classes from `red_etl/io/__init__.py`.
5. Add optional-dependency guards and unit tests.
