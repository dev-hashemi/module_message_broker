"""Redis Streams request/response implementation."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import redis.asyncio as redis
import structlog

from ..abstract import Message, RequestHandler
from .serializer import RedisMessageSerializer

logger = structlog.get_logger(__name__)


class RedisRequestResponseHandler:
    """Handles request/response messaging using Redis Streams."""

    def __init__(
        self,
        redis_client: redis.Redis,
        serializer: RedisMessageSerializer,
        consumer_group: str,
        consumer_name: str,
    ):
        """Initialize request/response handler.

        Args:
            redis_client: Redis client instance
            serializer: Message serializer
            consumer_group: Consumer group name
            consumer_name: Consumer name
        """
        self._redis_client = redis_client
        self._serializer = serializer
        self._consumer_group = consumer_group
        self._consumer_name = consumer_name
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._response_stream = f"responses.{consumer_name}"
        self._request_handlers: Dict[str, RequestHandler] = {}
        self._listening = False
        self._listen_task: Optional[asyncio.Task] = None

    async def request(self, message: Message, timeout: float = 30.0) -> Message:
        """Send a request and wait for response.

        Args:
            message: Request message
            timeout: Timeout in seconds

        Returns:
            Response message

        Raises:
            TimeoutError: If no response received within timeout
        """
        # Generate correlation ID and set reply-to
        correlation_id = str(uuid.uuid4())
        message.correlation_id = correlation_id
        message.reply_to = self._response_stream

        # Create future for response
        response_future = asyncio.Future()
        self._pending_requests[correlation_id] = response_future

        try:
            # Publish request
            fields = self._serializer.serialize(message)
            await self._redis_client.xadd(message.topic, fields)

            logger.debug(
                "Sent request message",
                topic=message.topic,
                correlation_id=correlation_id,
                reply_to=self._response_stream,
            )

            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            logger.warning(
                "Request timed out", correlation_id=correlation_id, timeout=timeout
            )
            raise TimeoutError(f"Request timed out after {timeout} seconds")
        finally:
            # Clean up pending request
            self._pending_requests.pop(correlation_id, None)

    async def handle_requests(self, topics: List[str], handler: RequestHandler) -> None:
        """Register handler for request topics.

        Args:
            topics: Topics to handle requests for
            handler: Request handler function
        """
        for topic in topics:
            self._request_handlers[topic] = handler

            # Create consumer group for the topic if it doesn't exist
            try:
                await self._redis_client.xgroup_create(
                    topic, self._consumer_group, id="0", mkstream=True
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

        logger.info("Registered request handlers", topics=topics)

    async def start_listening(self) -> None:
        """Start listening for responses and requests."""
        if self._listening:
            return

        self._listening = True

        # Create response stream and consumer group
        try:
            await self._redis_client.xgroup_create(
                self._response_stream, self._consumer_group, id="0", mkstream=True
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

        # Start listening task
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("Started request/response listener")

    async def stop_listening(self) -> None:
        """Stop listening for responses and requests."""
        if not self._listening:
            return

        self._listening = False

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped request/response listener")

    async def _listen_loop(self) -> None:
        """Main listening loop for responses and requests."""
        while self._listening:
            try:
                # Listen for responses on our response stream
                await self._process_responses()

                # Listen for requests on registered topics
                await self._process_requests()

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in request/response listen loop", error=str(e), exc_info=True
                )
                await asyncio.sleep(1)  # Back off on error

    async def _process_responses(self) -> None:
        """Process incoming responses."""
        try:
            # Read from response stream
            streams = await self._redis_client.xreadgroup(
                self._consumer_group,
                self._consumer_name,
                {self._response_stream: ">"},
                count=10,
                block=100,  # 100ms timeout
            )

            for stream_name, messages in streams:
                for message_id, fields in messages:
                    try:
                        # Deserialize message (all already strings with decode_responses=True)
                        message = self._serializer.deserialize(stream_name, message_id, fields)

                        # Find pending request
                        correlation_id = message.correlation_id
                        if correlation_id and correlation_id in self._pending_requests:
                            future = self._pending_requests[correlation_id]
                            if not future.done():
                                future.set_result(message)

                        # Acknowledge message
                        await self._redis_client.xack(
                            self._response_stream, self._consumer_group, message_id
                        )

                    except Exception as e:
                        logger.error(
                            "Error processing response message",
                            message_id=message_id,
                            error=str(e),
                            exc_info=True,
                        )

        except redis.ResponseError:
            # No messages available, continue
            pass

    async def _process_requests(self) -> None:
        """Process incoming requests."""
        if not self._request_handlers:
            return

        try:
            # Read from all request topics
            stream_dict = {topic: ">" for topic in self._request_handlers.keys()}

            streams = await self._redis_client.xreadgroup(
                self._consumer_group,
                self._consumer_name,
                stream_dict,
                count=10,
                block=100,  # 100ms timeout
            )

            for stream_name, messages in streams:
                topic = stream_name
                handler = self._request_handlers.get(topic)

                if not handler:
                    continue

                for message_id, fields in messages:
                    try:
                        # Deserialize request message (all already strings with decode_responses=True)
                        request_message = self._serializer.deserialize(topic, message_id, fields)

                        # Skip if this is a response message
                        if request_message.is_response:
                            await self._redis_client.xack(
                                topic, self._consumer_group, message_id
                            )
                            continue

                        # Process request
                        if request_message.correlation_id and request_message.reply_to:
                            response_message = await handler(request_message)

                            # Set response fields
                            response_message.correlation_id = (
                                request_message.correlation_id
                            )
                            response_message.is_response = True
                            response_message.message_id = str(uuid.uuid4())
                            response_message.timestamp = datetime.now(timezone.utc)

                            # Send response
                            response_fields = self._serializer.serialize(
                                response_message
                            )
                            await self._redis_client.xadd(
                                request_message.reply_to, response_fields
                            )

                            logger.debug(
                                "Sent response message",
                                correlation_id=request_message.correlation_id,
                                reply_to=request_message.reply_to,
                            )

                        # Acknowledge request message
                        await self._redis_client.xack(
                            topic, self._consumer_group, message_id
                        )

                    except Exception as e:
                        logger.error(
                            "Error processing request message",
                            topic=topic,
                            message_id=message_id,
                            error=str(e),
                            exc_info=True,
                        )

        except redis.ResponseError:
            # No messages available, continue
            pass
