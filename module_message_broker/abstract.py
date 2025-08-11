"""Abstract base classes for messaging infrastructure."""

import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from pydantic import BaseModel


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


# Backward compatibility alias
MessageTopic = PubSubTopic


@dataclass
class Message(abc.ABC):
    """Message data structure for inter-service communication.
    
    This class is an abstract base class that defines the structure of a message.
    It is not intended to be instantiated directly, but rather to be used as a base
    class for concrete message classes.
    """

    topic: Union[PubSubTopic, RequestTopic]
    data: Dict[str, Any]
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    is_response: bool = False

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
    topic: PubSubTopic = PubSubTopic.USER_CHAT_CREATE
    data: UserChatCreateSchema


class UserChatInteractionAddMessage(Message):
    """User chat interaction add message."""
    topic: PubSubTopic = PubSubTopic.USER_CHAT_INTERACTION_ADD
    data: UserChatInteractionAddSchema


# ============================================================================
# Request/Response Schemas
# ============================================================================

# LLM service schemas
class LLMGenerateTextRequestSchema(BaseModel):
    """Schema for LLM text generation requests."""
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    user_id: Optional[str] = None


class LLMGenerateTextResponseSchema(BaseModel):
    """Schema for LLM text generation responses."""
    success: bool
    generated_text: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class LLMGenerateStreamRequestSchema(BaseModel):
    """Schema for LLM streaming generation requests."""
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    user_id: Optional[str] = None


class LLMGenerateStreamResponseSchema(BaseModel):
    """Schema for LLM streaming generation responses."""
    success: bool
    stream_url: Optional[str] = None  # WebSocket or streaming endpoint
    session_id: Optional[str] = None
    error: Optional[str] = None


# ASR service schemas
class ASRTranscribeRequestSchema(BaseModel):
    """Schema for ASR transcription requests."""
    audio_file_path: str  # Path to audio file on shared storage
    language: Optional[str] = None
    user_id: Optional[str] = None


class ASRTranscribeResponseSchema(BaseModel):
    """Schema for ASR transcription responses."""
    success: bool
    transcription: Optional[str] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


# TTS service schemas
class TTSSynthesizeRequestSchema(BaseModel):
    """Schema for TTS synthesis requests."""
    text: str
    voice: Optional[str] = None
    language: Optional[str] = None
    speed: Optional[float] = None
    user_id: Optional[str] = None


class TTSSynthesizeResponseSchema(BaseModel):
    """Schema for TTS synthesis responses."""
    success: bool
    audio_path: Optional[str] = None  # Path to generated audio file
    error: Optional[str] = None


# ============================================================================
# Request/Response Message Classes
# ============================================================================

# LLM service messages
class LLMGenerateTextRequestMessage(Message):
    """LLM generate text request message."""
    topic: RequestTopic = RequestTopic.LLM_GENERATE_TEXT
    data: LLMGenerateTextRequestSchema


class LLMGenerateTextResponseMessage(Message):
    """LLM generate text response message."""
    topic: RequestTopic = RequestTopic.LLM_GENERATE_TEXT
    data: LLMGenerateTextResponseSchema
    is_response: bool = True


class LLMGenerateStreamRequestMessage(Message):
    """LLM generate stream request message."""
    topic: RequestTopic = RequestTopic.LLM_GENERATE_STREAM
    data: LLMGenerateStreamRequestSchema


class LLMGenerateStreamResponseMessage(Message):
    """LLM generate stream response message."""
    topic: RequestTopic = RequestTopic.LLM_GENERATE_STREAM
    data: LLMGenerateStreamResponseSchema
    is_response: bool = True


# ASR service messages
class ASRTranscribeRequestMessage(Message):
    """ASR transcribe request message."""
    topic: RequestTopic = RequestTopic.ASR_TRANSCRIBE_AUDIO
    data: ASRTranscribeRequestSchema


class ASRTranscribeResponseMessage(Message):
    """ASR transcribe response message."""
    topic: RequestTopic = RequestTopic.ASR_TRANSCRIBE_AUDIO
    data: ASRTranscribeResponseSchema
    is_response: bool = True


# TTS service messages
class TTSSynthesizeRequestMessage(Message):
    """TTS synthesize request message."""
    topic: RequestTopic = RequestTopic.TTS_SYNTHESIZE_SPEECH
    data: TTSSynthesizeRequestSchema


class TTSSynthesizeResponseMessage(Message):
    """TTS synthesize response message."""
    topic: RequestTopic = RequestTopic.TTS_SYNTHESIZE_SPEECH
    data: TTSSynthesizeResponseSchema
    is_response: bool = True


# Type alias for message handlers
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
