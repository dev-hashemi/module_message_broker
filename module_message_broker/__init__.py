"""Messaging infrastructure for inter-service communication."""

from .abstract import (
    MessageBroker, 
    Message, 
    MessageTopic,  # Backward compatibility alias for PubSubTopic
    PubSubTopic,
    RequestTopic,
    MessageHandler, 
    MessageSerializer, 
    RequestHandler
)
from .redis.broker import RedisMessageBroker
from .redis.serializer import RedisMessageSerializer
 
__all__ = [
    "MessageBroker", 
    "Message", 
    "MessageTopic",  # Backward compatibility
    "PubSubTopic",
    "RequestTopic",
    "MessageHandler",
    "RequestHandler",
    "MessageSerializer",
    "RedisMessageBroker",
    "RedisMessageSerializer",
] 