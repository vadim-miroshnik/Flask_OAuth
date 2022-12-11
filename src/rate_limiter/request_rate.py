"""Request rates for limiter."""

from enum import IntEnum

from rate_limiter.exceptions import ImmutableClassProperty


class ResetTypesEnum(IntEnum):
    SCHEDULED = 1
    INTERVAL = 2


class RequestRate:
    """Request rate definition."""

    def __init__(
        self,
        limit: int,
        interval: int,
        reset: ResetTypesEnum = ResetTypesEnum.INTERVAL,
    ):
        self._limit = limit
        self._interval = interval
        self._reset = reset
        self._log: dict[any, any] = {}

    @property
    def limit(self) -> int:
        return self._limit

    @limit.setter
    def limit(self, _):
        raise ImmutableClassProperty(self, "limit")

    @property
    def interval(self) -> int:
        return self._interval

    @interval.setter
    def interval(self, _):
        raise ImmutableClassProperty(self, "interval")

    def __str__(self):
        return f"{self.limit}/{self.interval}"
