"""Базовый класс корзины, используемой для ограничения запросов."""

from abc import ABC, abstractmethod


class AbstractBucket(ABC):
    """Базовый класс корзины."""

    def __init__(self, maxsize: int = 0, **kwargs):
        self._max_size = maxsize

    def maxsize(self) -> int:
        """Максимальный размер корзины."""
        return self._max_size

    @abstractmethod
    def size(self) -> int:
        """Текущий размер корзины."""
        pass

    @abstractmethod
    def put(self, item: float) -> int:
        """Внести объект в корзину."""
        pass

    @abstractmethod
    def get(self, number: int) -> int:
        """Получить количество объектов в корзине."""
        pass

    @abstractmethod
    def all_items(self) -> list[float]:
        """Все объекты в корзине."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Сбррс корзины."""
        pass

    def inspect_expired_items(self, time: float) -> tuple[int, float]:
        """Получение списка 'живых' объектов в корзине."""
        volume = self.size()
        item_count, remaining_time = 0, 0.0

        for log_idx, log_item in enumerate(self.all_items()):
            if log_item > time:
                item_count = volume - log_idx
                remaining_time = log_item - time
                break

        return item_count, remaining_time
