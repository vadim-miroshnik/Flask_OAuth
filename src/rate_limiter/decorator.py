"""Decorator for rate limiter."""

import asyncio
from flask import abort
from functools import partial
from functools import wraps
from inspect import iscoroutinefunction
from logging import getLogger
from time import sleep
from typing import Union

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
        """Allows usage as a decorator for both normal and async functions"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            self.delayed_acquire()
            try:
                return func(*args, **kwargs)
            except BucketFullException as err:
                abort(429, description="Too many requests")

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            await self.async_delayed_acquire()
            return await func(*args, **kwargs)

        # Return either an async or normal wrapper, depending on the type of the wrapped function
        return async_wrapper if iscoroutinefunction(func) else wrapper

    def delayed_acquire(self):
        """Delay and retry until we can successfully acquire an available bucket item"""
        while True:
            try:
                self.try_acquire()
            except BucketFullException as err:
                delay_time = self.delay_or_reraise(err)
                sleep(delay_time)
                abort(429, description="Too many requests")
            else:
                break

    async def async_delayed_acquire(self):
        """Delay and retry until we can successfully acquire an available bucket item"""
        while True:
            try:
                self.try_acquire()
            except BucketFullException as err:
                delay_time = self.delay_or_reraise(err)
                await asyncio.sleep(delay_time)
            else:
                break

    def delay_or_reraise(self, err: BucketFullException) -> float:
        """Determine if we should delay after exceeding a rate limit. If so, return the delay time,
        otherwise re-raise the exception.
        """
        delay_time = float(err.meta_info["remaining_time"])
        logger.debug(f"Rate limit reached; {delay_time:.5f} seconds remaining before next request")
        exceeded_max_delay = bool(self.max_delay) and (delay_time > self.max_delay)
        if self.delay and not exceeded_max_delay:
            return delay_time
        abort(429, description="Too many requests")

    def __enter__(self):
        """Allows usage as a contextmanager"""
        self.delayed_acquire()

    def __exit__(self, *exc):
        pass