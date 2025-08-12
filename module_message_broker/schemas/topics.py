"""Message topics for inter-service communication."""

from enum import Enum


class PubSubTopic(str, Enum):
    """Pub/Sub message topics for asynchronous event-driven communication."""

    # User service events
    USER_CHAT_CREATE = "user.chat.create"
    USER_CHAT_INTERACTION_ADD = "user.chat.interaction.add"


class RequestTopic(str, Enum):
    """Request/Response topics for synchronous inter-service communication."""
    
    # LLM service requests
    LLM_GENERATE_TEXT = "llm.generate.text"
    LLM_GENERATE_STREAM = "llm.generate.stream"
    
    # ASR service requests
    ASR_TRANSCRIBE_AUDIO = "asr.transcribe.audio"
    
    # TTS service requests
    TTS_SYNTHESIZE_SPEECH = "tts.synthesize.speech"