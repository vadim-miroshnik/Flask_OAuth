"""Реализация корзины с хранилищем в Redis."""

from core.redis import redis

from rate_limiter.bucket import AbstractBucket
from rate_limiter.exceptions import InvalidParams


class RedisBucket(AbstractBucket):
    """Корзина с хранением в Redis."""

    def __init__(
        self,
        maxsize=10,
        redis_pool=None,
        bucket_name: str = "test",
        identity: str = None,
        expire_time: int = None,
        **kwargs,
    ):
        super().__init__(maxsize=maxsize)

        if not bucket_name or not isinstance(bucket_name, str):
            raise InvalidParams(
                "keyword argument bucket-name is missing: a distinct name is required"
            )

        self._pool = redis_pool
        self._bucket_name = f"{bucket_name}___{identity}"
        self._expire_time = expire_time

    def get_connection(self):
        """Соединение с Redis."""
        return redis

    def get_pipeline(self):
        """Конвейер для групповых операций."""
        conn = self.get_connection()
        pipeline = conn.pipeline()
        return pipeline

    def size(self) -> int:
        conn = self.get_connection()
        return conn.llen(self._bucket_name)

    def put(self, item: float):
        conn = self.get_connection()
        current_size = conn.llen(self._bucket_name)

        if current_size < self.maxsize():
            pipeline = self.get_pipeline()
            pipeline.rpush(self._bucket_name, item)

            if self._expire_time is not None:
                pipeline.expire(self._bucket_name, self._expire_time)

            pipeline.execute()
            return 1

        return 0

    def get(self, number: int) -> int:
        pipeline = self.get_pipeline()
        counter = 0

        for _ in range(number):
            pipeline.lpop(self._bucket_name)
            counter += 1

        pipeline.execute()
        return counter

    def all_items(self) -> list[float]:
        conn = self.get_connection()
        items = conn.lrange(self._bucket_name, 0, -1)
        return sorted([float(i.decode("utf-8")) for i in items])

    def flush(self):
        conn = self.get_connection()
        conn.delete(self._bucket_name)
