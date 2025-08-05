"""Redis Streams implementation of the message broker."""

from typing import List, Optional

import redis.asyncio as redis
import structlog

from ..abstract import Message, MessageBroker, MessageHandler
from .consumer import RedisConsumer
from .publisher import RedisPublisher
from .serializer import RedisMessageSerializer

logger = structlog.get_logger(__name__)


class RedisMessageBroker(MessageBroker):
    """Redis Streams implementation of MessageBroker."""

    def __init__(
        self,
        redis_client: redis.Redis,
        consumer_group: str = "user_service",
        consumer_name: Optional[str] = None,
    ):
        """Initialize Redis message broker.

        Args:
            redis_client: Redis client instance
            consumer_group: Redis Stream consumer group name
            consumer_name: Unique consumer name (defaults to UUID)
        """
        # Initialize components
        self._serializer = RedisMessageSerializer()

        self._publisher = RedisPublisher(
            redis_client=redis_client, serializer=self._serializer
        )

        self._consumer = RedisConsumer(
            redis_client=redis_client,
            serializer=self._serializer,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
        )

    async def publish(self, message: Message) -> None:
        """Publish a message to a Redis Stream."""
        await self._publisher.publish(message)

    async def subscribe(self, topics: List[str], handler: MessageHandler) -> None:
        """Subscribe to Redis Stream topics."""
        await self._consumer.subscribe(topics, handler)

    async def unsubscribe(self, topics: List[str]) -> None:
        """Unsubscribe from Redis Stream topics."""
        await self._consumer.unsubscribe(topics)

    async def start_listening(self) -> None:
        """Start the Redis Stream listener process."""
        await self._consumer.start_listening()

    async def stop_listening(self) -> None:
        """Stop the Redis Stream listener process."""
        await self._consumer.stop_listening()
