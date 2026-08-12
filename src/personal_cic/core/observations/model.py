from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")


class ObservationStatus(str, Enum):
    """Truth status for one adapter observation.

    OBSERVED means the adapter successfully inspected the source and produced a
    complete normalized value. PARTIAL means a useful newly inspected value exists
    but one or more subordinate facts could not be observed. UNAVAILABLE means the
    source could not be inspected and no new domain value may be inferred from that
    failure. RETAINED means the latest inspection failed but an explicit source
    freshness policy still licenses the previously observed domain value for use.
    """

    OBSERVED = "observed"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"
    RETAINED = "retained"


class ObservationAvailability(str, Enum):
    CURRENT = "current"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RETAINED = "retained"


@dataclass(frozen=True, slots=True)
class Observation(Generic[T]):
    source: str
    status: ObservationStatus
    value: T | None = None
    detail: str | None = None

    @classmethod
    def observed(cls, source: str, value: T) -> "Observation[T]":
        return cls(source=source, status=ObservationStatus.OBSERVED, value=value)

    @classmethod
    def partial(cls, source: str, value: T, detail: str) -> "Observation[T]":
        return cls(
            source=source,
            status=ObservationStatus.PARTIAL,
            value=value,
            detail=detail,
        )

    @classmethod
    def unavailable(cls, source: str, detail: str) -> "Observation[T]":
        return cls(
            source=source,
            status=ObservationStatus.UNAVAILABLE,
            value=None,
            detail=detail,
        )

    @classmethod
    def retained(cls, source: str, detail: str) -> "Observation[T]":
        """No fresh sample arrived, but prior domain state remains usable by policy."""
        return cls(
            source=source,
            status=ObservationStatus.RETAINED,
            value=None,
            detail=detail,
        )
