"""Ограничитель запросов, использующий алгоритм протекающего ведра."""

from time import monotonic
from typing import Callable, Generic, TypeVar, Union

from rate_limiter.decorator import LimitDecorator
from rate_limiter.exceptions import BucketFullException, InvalidParams

T = TypeVar("T")


class Limiter(Generic[T]):
    """Ограничитель запросов."""

    def __init__(
        self,
        *rates: list[int],
        bucket_kwargs: dict[str, any] = None,
        time_function: Callable[[], float] = None,
    ):
        self._validate_rate_list(rates)
        self._rates = rates
        self._bucket_args = bucket_kwargs or {}
        self.bucket_group: dict[str, T] = {}
        self.time_function = monotonic
        if time_function is not None:
            self.time_function = time_function
        self.time_function()

    def _validate_rate_list(self, rates):
        """Валидация частоты запросов."""
        if not rates:
            raise InvalidParams("Rate(s) must be provided")

        for idx, rate in enumerate(rates[1:]):
            prev_rate = rates[idx]
            invalid = (
                rate <= prev_rate
            )
            if invalid:
                raise InvalidParams(f"{prev_rate} cannot come before {rate}")

    def _init_buckets(self, identities) -> None:
        """Инициализация корзины."""
        typ = self.__orig_class__.__args__[0]
        maxsize = self._rates[-1]
        for identity in sorted(identities):
            if not self.bucket_group.get(identity):
                self.bucket_group[identity] = typ(
                    maxsize=maxsize, identity=identity, **self._bucket_args,
                )

    def try_acquire(self, *identities: str) -> None:
        """Проверка на выполнение запроса."""
        self._init_buckets(identities)
        now = self.time_function()

        for rate in self._rates:
            for identity in identities:
                bucket = self.bucket_group[identity]
                volume = bucket.size()

                if volume < rate:
                    continue

                item_count, remaining_time = bucket.inspect_expired_items(
                    now - 1
                )
                if item_count >= rate:
                    raise BucketFullException(identity, rate, remaining_time)

                if rate is self._rates[-1]:
                    bucket.get(volume - item_count)

        for identity in identities:
            self.bucket_group[identity].put(now)

    def ratelimit(
        self,
        *identities: str,
        delay: bool = False,
        max_delay: Union[int, float] = None,
    ):
        """Вызов декоратора."""
        return LimitDecorator(self, *identities, delay=delay, max_delay=max_delay)

    def flush_all(self) -> int:
        """Очистка корзины."""
        cnt = 0

        for _, bucket in self.bucket_group.items():
            bucket.flush()
            cnt += 1

        return cnt
