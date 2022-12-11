"""Base bucket interface."""

from abc import ABC
from abc import abstractmethod


class AbstractBucket(ABC):
    """Base bucket interface."""

    def __init__(self, maxsize: int = 0, **kwargs):
        self._max_size = maxsize

    def maxsize(self) -> int:
        """Get max size of the bucket"""
        return self._max_size

    @abstractmethod
    def size(self) -> int:
        """Get current size of the bucket."""
        pass

    @abstractmethod
    def put(self, item: float) -> int:
        """Put current time in the bucket."""
        pass

    @abstractmethod
    def get(self, number: int) -> int:
        """Get items from the bucket."""
        pass

    @abstractmethod
    def all_items(self) -> list[float]:
        """Get all items in the bucket."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush bucket."""
        pass

    def inspect_expired_items(self, time: float) -> tuple[int, float]:
        """Number of unexpired items and next time to expire."""
        volume = self.size()
        item_count, remaining_time = 0, 0.0

        for log_idx, log_item in enumerate(self.all_items()):
            if log_item > time:
                item_count = volume - log_idx
                remaining_time = log_item - time
                break

        return item_count, remaining_time
