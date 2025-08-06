"""Shared test configuration and fixtures."""

import pytest
import pytest_asyncio
import redis.asyncio as redis
from module_message_broker import RedisMessageBroker


@pytest_asyncio.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    try:
        await client.ping()
        yield client
    except redis.ConnectionError:
        pytest.skip("Redis not available")
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def publisher_broker(redis_client):
    """Create publisher broker."""
    broker = RedisMessageBroker(
        redis_client=redis_client,
        consumer_group="test_publisher",
        consumer_name="pub_1"
    )
    await broker.start_listening()
    yield broker
    await broker.stop_listening()


@pytest_asyncio.fixture
async def subscriber_broker(redis_client):
    """Create subscriber broker."""
    broker = RedisMessageBroker(
        redis_client=redis_client,
        consumer_group="test_subscriber",
        consumer_name="sub_1"
    )
    await broker.start_listening()
    yield broker
    await broker.stop_listening()


@pytest_asyncio.fixture
async def client_broker(redis_client):
    """Create client broker for requests."""
    broker = RedisMessageBroker(
        redis_client=redis_client,
        consumer_group="test_client",
        consumer_name="client_1"
    )
    await broker.start_listening()
    yield broker
    await broker.stop_listening()


@pytest_asyncio.fixture
async def server_broker(redis_client):
    """Create server broker for handling requests."""
    broker = RedisMessageBroker(
        redis_client=redis_client,
        consumer_group="test_server",
        consumer_name="server_1"
    )
    await broker.start_listening()
    yield broker
    await broker.stop_listening()