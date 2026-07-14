"""Message schemas for inter-service communication."""

# Import topics first (no dependencies)
from .topics import PubSubTopic, ReqResTopic

# Import schema classes (depend on topics but not on message classes)
from .llm_schemas import (
    LLMGenerateRequestSchema,
    LLMGenerateResponseSchema
)

from .user_schemas import (
    UserDeletedEventSchema
)

# Import message classes last (depend on both topics and core.message)
from .llm_schemas import (
    LLMGenerateRequestMessage,
    LLMGenerateResponseMessage,
    LLMGenerateMultipartResponseMessage
)

from .user_schemas import (
    UserDeletedEventMessage
)

__all__ = [
    # Topics
    "PubSubTopic",
    "ReqResTopic",
    
    # LLM schemas
    "LLMGenerateRequestSchema",
    "LLMGenerateResponseSchema",
    "LLMGenerateRequestMessage",
    "LLMGenerateResponseMessage",
    "LLMGenerateMultipartResponseMessage",
    
    # User schemas
    "UserDeletedEventSchema",
    "UserDeletedEventMessage"
]
