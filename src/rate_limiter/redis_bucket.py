"""Redis bucket implementation."""

from rate_limiter.bucket import AbstractBucket
from core.redis import redis
from rate_limiter.exceptions import InvalidParams


class RedisBucket(AbstractBucket):

    def __init__(
        self,
        maxsize=10,
        redis_pool=None,
        bucket_name: str = "test",
        identity: str = None,
        expire_time: int = None,
        **kwargs,
    ):
        if not bucket_name or not isinstance(bucket_name, str):
            raise InvalidParams("keyword argument bucket-name is missing: a distinct name is required")

        self.maxsize = maxsize
        self.pool = redis_pool
        self.bucket_name = f"{bucket_name}___{identity}"
        self.expire_time = expire_time

    def get_connection(self):
        return redis

    def get_pipeline(self):
        conn = self.get_connection()
        pipeline = conn.pipeline()
        return pipeline

    def size(self) -> int:
        conn = self.get_connection()
        return conn.llen(self.bucket_name)

    def put(self, item: float):
        conn = self.get_connection()
        current_size = conn.llen(self.bucket_name)

        if current_size < self.maxsize:
            pipeline = self.get_pipeline()
            pipeline.rpush(self.bucket_name, item)

            if self.expire_time is not None:
                pipeline.expire(self.bucket_name, self.expire_time)

            pipeline.execute()
            return 1

        return 0

    def get(self, number: int) -> int:
        pipeline = self.get_pipeline()
        counter = 0

        for _ in range(number):
            pipeline.lpop(self.bucket_name)
            counter += 1

        pipeline.execute()
        return counter

    def all_items(self) -> list[float]:
        conn = self.get_connection()
        items = conn.lrange(self.bucket_name, 0, -1)
        return sorted([float(i.decode("utf-8")) for i in items])

    def flush(self):
        conn = self.get_connection()
        conn.delete(self.bucket_name)
