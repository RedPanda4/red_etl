"""Abstract base classes for data sources and sinks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from red_etl.backends.base import Backend


class Source(ABC):
    """Abstract base class for a data source.

    A source knows how to read data from a specific location or system
    (local file, S3, database, etc.) and return it in the native format of
    a chosen backend.

    Sources are optional I/O building blocks. They are intentionally separated
    from the core transformation engine so that reading, writing and cleaning
    can evolve independently.

    """

    @abstractmethod
    def read(self, backend: Backend) -> Any:
        """Read data and return it in the native format of ``backend``.

        Parameters
        ----------
        backend
            The backend that will consume the data.

        Returns
        -------
        Any
            Dataset in the backend's native format.
        """


class Sink(ABC):
    """Abstract base class for a data sink.

    A sink knows how to write data in the native format of a chosen backend
    to a specific location or system.

    Sinks are optional I/O building blocks. They are intentionally separated
    from the core transformation engine.

    """

    @abstractmethod
    def write(self, data: Any, backend: Backend) -> None:
        """Write ``data`` to the sink using the supplied backend's format.

        Parameters
        ----------
        data
            Dataset in the backend's native format.
        backend
            The backend that produced the data.
        """
