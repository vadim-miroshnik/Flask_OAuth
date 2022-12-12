"""Декоратор для ограничителя запросов."""

from functools import partial, wraps
from logging import getLogger
from time import sleep
from typing import Union

from flask import abort

from rate_limiter.exceptions import BucketFullException

logger = getLogger(__name__)


class LimitDecorator:
    def __init__(
        self,
        limiter: "Limiter",
        *identities: str,
        delay: bool = False,
        max_delay: Union[int, float] = None,
    ):
        self.delay = delay
        self.max_delay = max_delay or 0
        self.try_acquire = partial(limiter.try_acquire, *identities)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.delayed_acquire()
            try:
                return func(*args, **kwargs)
            except BucketFullException as err:
                abort(429, description="Too many requests")

        return wrapper

    def delayed_acquire(self):
        """Вызов запроса."""
        while True:
            try:
                self.try_acquire()
            except BucketFullException as err:
                delay_time = self.delay_or_reraise(err)
                sleep(delay_time)
                abort(429, description="Too many requests")
            else:
                break

    def delay_or_reraise(self, err: BucketFullException) -> float:
        """Задержка выполнения запроса или вызов исключения."""
        delay_time = float(err.meta_info["remaining_time"])
        logger.debug(
            f"Rate limit reached; {delay_time:.5f} seconds remaining before next request"
        )
        exceeded_max_delay = bool(self.max_delay) and (delay_time > self.max_delay)
        if self.delay and not exceeded_max_delay:
            return delay_time
        abort(429, description="Too many requests")

    def __enter__(self):
        self.delayed_acquire()

    def __exit__(self, *exc):
        pass
