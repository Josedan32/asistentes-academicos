from typing import cast
from uuid import uuid4

from redis.asyncio import Redis

QUEUE_KEY = "inference:queue"
SEQUENCE_KEY = "inference:seq"


class RedisInferenceGate:
    """A sorted set keyed by an ever-increasing sequence number gives FIFO order and an
    O(log n) position lookup (ZRANK), atomically, without a separate lock — Redis is
    single-threaded (spec §8.2)."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def enqueue(self) -> str:
        ticket = uuid4().hex
        sequence = await self._redis.incr(SEQUENCE_KEY)
        await self._redis.zadd(QUEUE_KEY, {ticket: sequence})
        return ticket

    async def position(self, ticket: str) -> int | None:
        rank = await self._redis.zrank(QUEUE_KEY, ticket)
        return None if rank is None else cast(int, rank) + 1

    async def release(self, ticket: str) -> None:
        await self._redis.zrem(QUEUE_KEY, ticket)
