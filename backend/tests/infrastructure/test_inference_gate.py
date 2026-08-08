import pytest
from fakeredis import FakeAsyncRedis
from redis.asyncio import Redis

from app.infrastructure.redis.inference_gate import RedisInferenceGate


@pytest.fixture
async def gate():
    redis = FakeAsyncRedis()
    yield RedisInferenceGate(redis)
    await redis.aclose()


async def test_the_first_ticket_gets_position_one(gate: RedisInferenceGate) -> None:
    ticket = await gate.enqueue()
    assert await gate.position(ticket) == 1


async def test_a_second_ticket_queues_behind_the_first(gate: RedisInferenceGate) -> None:
    first = await gate.enqueue()
    second = await gate.enqueue()
    assert await gate.position(first) == 1
    assert await gate.position(second) == 2


async def test_releasing_the_head_advances_the_queue(gate: RedisInferenceGate) -> None:
    first = await gate.enqueue()
    second = await gate.enqueue()
    await gate.release(first)
    assert await gate.position(second) == 1


async def test_a_released_ticket_has_no_position(gate: RedisInferenceGate) -> None:
    ticket = await gate.enqueue()
    await gate.release(ticket)
    assert await gate.position(ticket) is None


@pytest.mark.redis
async def test_the_gate_works_against_a_real_redis_instance() -> None:
    redis = Redis.from_url("redis://localhost:6379/1")
    gate = RedisInferenceGate(redis)
    ticket = await gate.enqueue()
    try:
        assert await gate.position(ticket) == 1
    finally:
        await gate.release(ticket)
        await redis.aclose()
