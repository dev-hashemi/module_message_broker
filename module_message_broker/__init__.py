"""Messaging infrastructure for inter-service communication."""

# Import core components
from .core import (
    MessageBroker, 
    Message, 
    MessageHandler, 
    MessageSerializer, 
    RequestHandler
)

# Import schemas (including topics)
from .schemas import (
    PubSubTopic,
    RequestTopic
)

# Import Redis implementation
from .redis.broker import RedisMessageBroker
from .redis.serializer import RedisMessageSerializer

# Import all schemas for convenience
from .schemas import *
 
__all__ = [
    # Core components
    "MessageBroker", 
    "Message", 
    "MessageHandler",
    "RequestHandler",
    "MessageSerializer",
    
    # Topics (from schemas)
    "PubSubTopic",
    "RequestTopic",
    
    # Redis implementation
    "RedisMessageBroker",
    "RedisMessageSerializer",
    
    # All schemas are exported via schemas.__init__.py
] 