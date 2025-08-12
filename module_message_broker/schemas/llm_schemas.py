"""LLM service message schemas."""

from typing import Optional
from pydantic import BaseModel

from ..core.message import Message
from .topics import RequestTopic


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