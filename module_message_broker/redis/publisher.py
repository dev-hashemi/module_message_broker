"""Redis Streams publisher implementation."""

import uuid
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
import structlog

from ..core.message import Message
from .serializer import RedisMessageSerializer

logger = structlog.get_logger(__name__)


class RedisPublisher:
    """Manages Redis Streams publishing operations."""

    def __init__(self, redis_client: redis.Redis, serializer: RedisMessageSerializer):
        """Initialize Redis publisher.

        Args:
            connection: Redis connection instance
            serializer: Message serializer for Redis
        """
        self._redis_client = redis_client
        self._serializer = serializer

    async def publish(self, message: Message) -> Optional[str]:
        """Publish a message to a Redis Stream.

        Args:
            message: Message to publish

        Returns:
            Entry ID if successful, None on error

        Raises:
            RuntimeError: If not connected to Redis
            redis.RedisError: If there is an error publishing the message
        """
        redis_client = self._redis_client
        if redis_client is None:
            logger.error("Cannot publish message: Not connected to Redis")
            raise RuntimeError("Not connected to Redis")

        # Ensure message has ID
        if message.message_id is None:
            message.message_id = str(uuid.uuid4())

        # Ensure message has timestamp
        if message.timestamp is None:
            message.timestamp = datetime.utcnow()

        # Use serializer to convert message to Redis format
        fields = self._serializer.serialize(message)

        # Stream key is the topic
        stream_key = message.topic

        # Add to stream with auto-generated ID
        try:
            logger.debug(
                "Publishing message to Redis stream",
                stream=stream_key,
                message_id=message.message_id,
            )

            entry_id = await redis_client.xadd(
                stream_key,
                fields,
                maxlen=1000,  # Keep last 1000 messages
                approximate=True,  # Approximate trimming for better performance
            )

            logger.debug(
                "Message published successfully",
                stream=stream_key,
                message_id=message.message_id,
                entry_id=entry_id,
            )

            return entry_id

        except redis.RedisError as e:
            logger.error(
                "Failed to publish message to Redis stream",
                error=str(e),
                stream=stream_key,
                message_id=message.message_id,
                exc_info=True,
            )
            raise
