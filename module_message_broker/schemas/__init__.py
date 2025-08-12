"""Message schemas for inter-service communication."""

# Import topics first (no dependencies)
from .topics import PubSubTopic, RequestTopic

# Import schema classes (depend on topics but not on message classes)
from .user_schemas import (
    UserChatCreateSchema,
    UserChatInteractionAddSchema
)

from .llm_schemas import (
    LLMGenerateTextRequestSchema,
    LLMGenerateTextResponseSchema,
    LLMGenerateStreamRequestSchema,
    LLMGenerateStreamResponseSchema
)

from .asr_schemas import (
    ASRTranscribeRequestSchema,
    ASRTranscribeResponseSchema
)

from .tts_schemas import (
    TTSSynthesizeRequestSchema,
    TTSSynthesizeResponseSchema
)

# Import message classes last (depend on both topics and core.message)
from .user_schemas import (
    UserChatCreateMessage,
    UserChatInteractionAddMessage
)

from .llm_schemas import (
    LLMGenerateTextRequestMessage,
    LLMGenerateTextResponseMessage,
    LLMGenerateStreamRequestMessage,
    LLMGenerateStreamResponseMessage
)

from .asr_schemas import (
    ASRTranscribeRequestMessage,
    ASRTranscribeResponseMessage
)

from .tts_schemas import (
    TTSSynthesizeRequestMessage,
    TTSSynthesizeResponseMessage
)

__all__ = [
    # Topics
    "PubSubTopic",
    "RequestTopic",
    
    # User schemas
    "UserChatCreateSchema",
    "UserChatInteractionAddSchema", 
    "UserChatCreateMessage",
    "UserChatInteractionAddMessage",
    
    # LLM schemas
    "LLMGenerateTextRequestSchema",
    "LLMGenerateTextResponseSchema",
    "LLMGenerateStreamRequestSchema", 
    "LLMGenerateStreamResponseSchema",
    "LLMGenerateTextRequestMessage",
    "LLMGenerateTextResponseMessage",
    "LLMGenerateStreamRequestMessage",
    "LLMGenerateStreamResponseMessage",
    
    # ASR schemas
    "ASRTranscribeRequestSchema",
    "ASRTranscribeResponseSchema",
    "ASRTranscribeRequestMessage",
    "ASRTranscribeResponseMessage",
    
    # TTS schemas
    "TTSSynthesizeRequestSchema",
    "TTSSynthesizeResponseSchema",
    "TTSSynthesizeRequestMessage", 
    "TTSSynthesizeResponseMessage"
]