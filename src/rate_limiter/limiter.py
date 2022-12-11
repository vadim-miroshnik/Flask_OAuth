"""Limiter of requests using Leacky Bucket algorithm."""

from time import monotonic
from typing import Any
from typing import Callable
from typing import Union
from enum import IntEnum
from typing import TypeVar, Generic

from rate_limiter.exceptions import InvalidParams
from rate_limiter.exceptions import BucketFullException
from rate_limiter.request_rate import RequestRate
from rate_limiter.redis_bucket import RedisBucket
from rate_limiter.decorator import LimitDecorator

T = TypeVar("T")


class DurationEnum(IntEnum):
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 3600 * 24
    MONTH = 3600 * 24 * 30


class Limiter(Generic[T]):

    def __init__(
        self,
        *rates: RequestRate,
        bucket_class: type = RedisBucket,
        bucket_kwargs: dict[str, any] = None,
        time_function: Callable[[], float] = None,
    ):
        self.validate_rate_list(rates)
        self.rates = rates
        self.bucket_args = bucket_kwargs or {}
        self.bucket_group: dict[str, RedisBucket] = {}
        self.time_function = monotonic
        if time_function is not None:
            self.time_function = time_function
        self.time_function()

    def validate_rate_list(self, rates):
        if not rates:
            raise InvalidParams("Rate(s) must be provided")

        for idx, rate in enumerate(rates[1:]):
            prev_rate = rates[idx]
            invalid = rate.limit <= prev_rate.limit or rate.interval <= prev_rate.interval
            if invalid:
                raise InvalidParams(f"{prev_rate} cannot come before {rate}")

    def init_buckets(self, identities) -> None:
        typ = self.__orig_class__.__args__[0]
        maxsize = self.rates[-1].limit
        for identity in sorted(identities):
            if not self.bucket_group.get(identity):
                self.bucket_group[identity] = typ(
                    maxsize=maxsize,
                    identity=identity,
                    **self.bucket_args,
                )

    def try_acquire(self, *identities: str) -> None:
        self.init_buckets(identities)
        now = self.time_function()

        for rate in self.rates:
            for identity in identities:
                bucket = self.bucket_group[identity]
                volume = bucket.size()

                if volume < rate.limit:
                    continue

                item_count, remaining_time = bucket.inspect_expired_items(now - rate.interval)
                if item_count >= rate.limit:
                    raise BucketFullException(identity, rate, remaining_time)

                if rate is self.rates[-1]:
                    bucket.get(volume - item_count)

        for identity in identities:
            self.bucket_group[identity].put(now)

    def ratelimit(
        self,
        *identities: str,
        delay: bool = False,
        max_delay: Union[int, float] = None,
    ):
        return LimitDecorator(self, *identities, delay=delay, max_delay=max_delay)

    def get_current_volume(self, identity) -> int:
        bucket = self.bucket_group[identity]
        return bucket.size()

    def flush_all(self) -> int:
        cnt = 0

        for _, bucket in self.bucket_group.items():
            bucket.flush()
            cnt += 1

        return cnt
