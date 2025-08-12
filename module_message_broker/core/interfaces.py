"""Abstract interfaces for message broker components."""

import abc
from typing import Awaitable, Callable, Dict, List

from .message import Message


# Type aliases for message handlers
MessageHandler = Callable[[Message], Awaitable[None]]
RequestHandler = Callable[[Message], Awaitable[Message]]


class MessageSerializer(abc.ABC):
    """Abstract base class for message serialization/deserialization."""

    @abc.abstractmethod
    def serialize(self, message: Message) -> Dict[str, str]:
        """Convert Message object to broker-specific format.

        Args:
            message: Message to serialize

        Returns:
            Dictionary with string keys and values for broker storage
        """
        pass

    @abc.abstractmethod
    def deserialize(self, topic: str, message_id: str, data: Dict[str, str]) -> Message:
        """Convert broker-specific format to Message object.

        Args:
            topic: Message topic
            message_id: Unique message identifier
            data: Raw message data from broker

        Returns:
            Deserialized Message object
        """
        pass


class MessageBroker(abc.ABC):
    """Abstract base class for message brokers."""

    @abc.abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish a message to a topic."""
        pass

    @abc.abstractmethod
    async def subscribe(self, topics: List[str], handler: MessageHandler) -> None:
        """Subscribe to one or more topics.

        Args:
            topics: List of topics to subscribe to
            handler: Async callback function to handle received messages
        """
        pass

    @abc.abstractmethod
    async def unsubscribe(self, topics: List[str]) -> None:
        """Unsubscribe from one or more topics.

        Args:
            topics: List of topics to unsubscribe from
        """
        pass

    @abc.abstractmethod
    async def start_listening(self) -> None:
        """Start the message listener process."""
        pass

    @abc.abstractmethod
    async def stop_listening(self) -> None:
        """Stop the message listener process."""
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def handle_requests(self, topics: List[str], handler: RequestHandler) -> None:
        """Handle request messages on specified topics.
        
        Args:
            topics: List of topics to handle requests for
            handler: Async callback function that processes requests and returns responses
        """
        pass