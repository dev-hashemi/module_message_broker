"""LLM service message schemas."""

from typing import Optional

from pydantic import BaseModel

from ..core.message import Message
from ..core.multipart_message import MultipartMessage
from .topics import RequestTopic


class LLMGenerateRequestSchema(BaseModel):
    """Schema for LLM Generate requests."""

    prompt: str
    model: Optional[str] = "tida"
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class LLMGenerateResponseSchema(BaseModel):
    """Schema for LLM Generate responses."""

    success: bool
    response_text: Optional[str] = None
    model_used: Optional[str] = None
    chat_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class LLMGenerateRequestMessage(Message):
    """LLM Generate request message."""

    topic: RequestTopic = RequestTopic.LLM_GENERATE_TEXT
    data: LLMGenerateRequestSchema


class LLMGenerateResponseMessage(Message):
    """LLM Generate response message."""

    topic: RequestTopic = RequestTopic.LLM_GENERATE_TEXT
    data: LLMGenerateResponseSchema
    is_response: bool = True


class LLMGenerateMultipartResponseMessage(MultipartMessage):
    """LLM Generate Multipart response message."""

    topic: RequestTopic = RequestTopic.LLM_GENERATE_TEXT
    data: LLMGenerateResponseSchema
