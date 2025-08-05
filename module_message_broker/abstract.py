"""Abstract base classes for messaging infrastructure."""

import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from pydantic import BaseModel


class MessageTopic(str, Enum):
    """Standard message topics for the application."""

    # User service topics
    USER_CHAT_CREATE = "user.chat.create"
    USER_CHAT_INTERACTION_ADD = "user.chat.interaction.add"


@dataclass
class Message(abc.ABC):
    """Message data structure for inter-service communication.
    
    This class is an abstract base class that defines the structure of a message.
    It is not intended to be instantiated directly, but rather to be used as a base
    class for concrete message classes.
    """

    topic: MessageTopic
    data: Dict[str, Any]
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None


    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


class UserChatCreateSchema(BaseModel):
    user_id: str
    question: str
    answer: str
    chat_id: str


class UserChatInteractionAddSchema(BaseModel):
    user_id: str
    question: str
    answer: str
    chat_id: str


class UserChatCreateMessage(Message):
    """User chat create message."""
    topic: MessageTopic = MessageTopic.USER_CHAT_CREATE
    data: UserChatCreateSchema


class UserChatInteractionAddMessage(Message):
    """User chat interaction add message."""
    topic: MessageTopic = MessageTopic.USER_CHAT_INTERACTION_ADD
    data: UserChatInteractionAddSchema


# Type alias for message handlers
MessageHandler = Callable[[Message], Awaitable[None]]


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
