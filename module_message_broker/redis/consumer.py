"""Redis Streams consumer implementation."""

import asyncio
import uuid
from typing import Dict, List, Optional, Set

import redis.asyncio as redis
import structlog

from ..core.interfaces import MessageHandler
from .serializer import RedisMessageSerializer

logger = structlog.get_logger(__name__)


class RedisConsumer:
    """Manages Redis Streams consumer operations."""

    def __init__(
        self,
        redis_client: redis.Redis,
        serializer: RedisMessageSerializer,
        consumer_group: str = "user_service",
        consumer_name: Optional[str] = None,
    ):
        """Initialize Redis consumer.

        Args:
            connection: Redis connection instance
            serializer: Message serializer for Redis
            consumer_group: Redis Stream consumer group name
            consumer_name: Unique consumer name (defaults to UUID)
        """
        self._redis_client = redis_client
        self._serializer = serializer
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name or f"consumer-{uuid.uuid4()}"

        self._subscribed_topics: Set[str] = set()
        self._message_handlers: Dict[str, List[MessageHandler]] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False

    async def subscribe(self, topics: List[str], handler: MessageHandler) -> None:
        """Subscribe to Redis Stream topics.

        Args:
            topics: List of topics to subscribe to
            handler: Async callback function to handle received messages

        Raises:
            RuntimeError: If not connected to Redis
        """
        redis_client = self._redis_client
        if redis_client is None:
            logger.error("Cannot subscribe: Not connected to Redis")
            raise RuntimeError("Not connected to Redis")

        for topic in topics:
            # Create consumer group if it doesn't exist
            try:
                # Check if stream exists first
                if not await redis_client.exists(topic):
                    # Create an empty stream with a message that will be ignored
                    await redis_client.xadd(topic, {"_init": "1"})
                    logger.info(f"Created new stream for topic: {topic}")

                # Create consumer group
                await redis_client.xgroup_create(
                    topic,
                    self._consumer_group,
                    id="0",  # Start from beginning of stream
                    mkstream=True,  # Create stream if it doesn't exist
                )
                logger.info(
                    "Created consumer group for topic",
                    topic=topic,
                    group=self._consumer_group,
                )
            except redis.ResponseError as e:
                # Group already exists, which is fine
                if "BUSYGROUP" not in str(e):
                    logger.warning(
                        "Error creating consumer group", topic=topic, error=str(e)
                    )

            # Add to subscribed topics
            self._subscribed_topics.add(topic)

            # Add handler to the topic
            if topic not in self._message_handlers:
                self._message_handlers[topic] = []
            self._message_handlers[topic].append(handler)

            logger.info(
                "Subscribed to topic",
                topic=topic,
                group=self._consumer_group,
                consumer=self._consumer_name,
            )

    async def unsubscribe(self, topics: List[str]) -> None:
        """Unsubscribe from Redis Stream topics.

        Args:
            topics: List of topics to unsubscribe from
        """
        for topic in topics:
            if topic in self._subscribed_topics:
                self._subscribed_topics.remove(topic)
                # Remove handlers for this topic
                self._message_handlers.pop(topic, None)
                logger.info("Unsubscribed from topic", topic=topic)

    async def start_listening(self) -> None:
        """Start the Redis Stream listener process.

        This creates an asyncio task that continuously polls for new messages.
        """
        if self._redis_client is None:
            logger.error("Cannot start listener: Not connected to Redis")
            raise RuntimeError("Not connected to Redis")

        if self._listener_task is not None:
            # Already running
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_for_messages())
        logger.info(
            "Started Redis Stream listener",
            consumer_group=self._consumer_group,
            consumer=self._consumer_name,
        )

    async def stop_listening(self) -> None:
        """Stop the Redis Stream listener process."""
        if self._listener_task is None:
            return

        self._running = False

        # Wait for listener task to complete
        try:
            await asyncio.wait_for(self._listener_task, timeout=5.0)
        except asyncio.TimeoutError:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        self._listener_task = None
        logger.info("Stopped Redis Stream listener")

    async def _listen_for_messages(self) -> None:
        """Listen for messages on all subscribed topics."""
        redis_client = self._redis_client
        if redis_client is None:
            logger.error("Cannot listen for messages: Not connected to Redis")
            return

        while self._running:
            if not self._subscribed_topics:
                # No topics to listen to, sleep and continue
                await asyncio.sleep(1)
                continue

            try:
                # Create streams dict for xreadgroup: {stream: last_id}
                streams = {topic: ">" for topic in self._subscribed_topics}

                # Read messages from streams
                response = await redis_client.xreadgroup(
                    groupname=self._consumer_group,
                    consumername=self._consumer_name,
                    streams=streams,
                    count=10,  # Process up to 10 messages at a time
                    block=1000,  # Block for 1 second, then retry
                )

                if not response:
                    # No messages available
                    continue

                # Process messages
                for stream_data in response:
                    topic = stream_data[0]  # Stream name (topic)
                    entries = stream_data[1]  # List of [id, fields] entries

                    for entry_id, fields in entries:
                        # Use serializer to convert Redis entry to Message object
                        message = self._serializer.deserialize(topic, entry_id, fields)

                        # Call handlers for this topic
                        handlers = self._message_handlers.get(topic, [])
                        if not handlers:
                            logger.warning(
                                "Received message for topic with no handlers",
                                topic=topic,
                            )
                            continue

                        for handler in handlers:
                            try:
                                await handler(message)
                            except Exception as e:
                                logger.error(
                                    "Error in message handler",
                                    topic=topic,
                                    error=str(e),
                                    exc_info=True,
                                )

                        # Acknowledge message processing
                        await redis_client.xack(topic, self._consumer_group, entry_id)

            except redis.RedisError as e:
                logger.error(
                    "Error in Redis Stream listener", error=str(e), exc_info=True
                )
                # Sleep before retrying to avoid tight loop on errors
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(
                    "Unexpected error in message listener", error=str(e), exc_info=True
                )
                await asyncio.sleep(1)
