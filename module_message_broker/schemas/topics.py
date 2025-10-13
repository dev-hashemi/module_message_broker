"""Message topics for inter-service communication."""

from enum import Enum


class PubSubTopic(str, Enum):
    """Pub/Sub message topics for asynchronous event-driven communication."""

    # Service communication topics
    ASR_REQUEST = "asr.request"
    ASR_RESPONSE = "asr.response"
    TTS_REQUEST = "tts.request"
    TTS_RESPONSE = "tts.response"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    
    # User service events
    USER_SOFT_DELETED = "user.soft_deleted"
    


class ReqResTopic(str, Enum):
    """Request/Response topics for synchronous inter-service communication."""

    # LLM service requests
    LLM_GENERATE_TEXT = "llm.generate.text"

    # ASR service requests
    ASR_TRANSCRIBE_AUDIO = "asr.transcribe.audio"

    # TTS service requests
    TTS_SYNTHESIZE_SPEECH = "tts.synthesize.speech"


