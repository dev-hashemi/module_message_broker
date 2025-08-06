"""Redis Streams implementation of the message broker."""

from typing import List, Optional

import redis.asyncio as redis
import structlog

from ..abstract import Message, MessageBroker, MessageHandler, RequestHandler
from .consumer import RedisConsumer
from .publisher import RedisPublisher
from .serializer import RedisMessageSerializer
from .request_response import RedisRequestResponseHandler

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
        
        self._request_response = RedisRequestResponseHandler(
            redis_client=redis_client,
            serializer=self._serializer,
            consumer_group=consumer_group,
            consumer_name=consumer_name or self._consumer._consumer_name,
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
        await self._request_response.start_listening()

    async def stop_listening(self) -> None:
        """Stop the Redis Stream listener process."""
        await self._consumer.stop_listening()
        await self._request_response.stop_listening()

    async def request(self, message: Message, timeout: float = 30.0) -> Message:
        """Send a request message and wait for a response.
        
        Args:
            message: Request message to send
            timeout: Maximum time to wait for response in seconds
            
        Returns:
            Response message
            
        Raises:
            TimeoutError: If no response received within timeout
            RuntimeError: If broker is not connected or other errors
        """
        return await self._request_response.request(message, timeout)

    async def handle_requests(self, topics: List[str], handler: RequestHandler) -> None:
        """Handle request messages on specified topics.
        
        Args:
            topics: List of topics to handle requests for
            handler: Async callback function that processes requests and returns responses
        """
        await self._request_response.handle_requests(topics, handler)
