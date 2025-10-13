"""TTS service message schemas."""

from typing import Optional
from pydantic import BaseModel, field_validator

from ..core.message import Message
from .topics import ReqResTopic


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


class TTSSynthesizeRequestMessage(Message):
    """TTS synthesize request message."""
    topic: ReqResTopic = ReqResTopic.TTS_SYNTHESIZE_SPEECH
    
    @field_validator('data', mode='before')
    @classmethod
    def validate_data(cls, v):
        if isinstance(v, TTSSynthesizeRequestSchema):
            return v.model_dump()
        return v


class TTSSynthesizeResponseMessage(Message):
    """TTS synthesize response message."""
    topic: ReqResTopic = ReqResTopic.TTS_SYNTHESIZE_SPEECH
    is_response: bool = True
    
    @field_validator('data', mode='before')
    @classmethod
    def validate_data(cls, v):
        if isinstance(v, TTSSynthesizeResponseSchema):
            return v.model_dump()
        return v