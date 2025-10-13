"""Shared test configuration and fixtures."""

import pytest
import pytest_asyncio
import redis.asyncio as redis
from module_message_broker import RedisMessageBroker


async def _cleanup_test_streams(redis_client):
    """Helper to clean up test streams and consumer groups."""
    test_topics = [
        "llm.request", "llm.response", "asr.request", "asr.response",
        "tts.request", "tts.response", "llm.generate.text"
    ]
    
    for topic in test_topics:
        try:
            # Get all consumer groups for this stream
            try:
                groups = await redis_client.xinfo_groups(topic)
                for group_info in groups:
                    group_name = group_info['name']
                    try:
                        # Delete the consumer group
                        await redis_client.xgroup_destroy(topic, group_name)
                    except Exception:
                        pass  # Group might not exist
            except Exception:
                pass  # Stream might not exist
            
            # Delete the stream (removes all messages)
            await redis_client.delete(topic)
        except Exception:
            # Stream might not exist, ignore errors
            pass


@pytest_asyncio.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    try:
        await client.ping()
        # Clean up before tests
        await _cleanup_test_streams(client)
        yield client
        # Clean up after tests 
        await _cleanup_test_streams(client)
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