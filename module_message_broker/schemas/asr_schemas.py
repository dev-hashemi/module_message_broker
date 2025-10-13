"""ASR service message schemas."""

from typing import Optional
from pydantic import BaseModel, field_validator

from ..core.message import Message
from .topics import ReqResTopic


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


class ASRTranscribeRequestMessage(Message):
    """ASR transcribe request message."""
    topic: ReqResTopic = ReqResTopic.ASR_TRANSCRIBE_AUDIO
    
    @field_validator('data', mode='before')
    @classmethod
    def validate_data(cls, v):
        if isinstance(v, ASRTranscribeRequestSchema):
            return v.model_dump()
        return v


class ASRTranscribeResponseMessage(Message):
    """ASR transcribe response message."""
    topic: ReqResTopic = ReqResTopic.ASR_TRANSCRIBE_AUDIO
    is_response: bool = True
    
    @field_validator('data', mode='before')
    @classmethod
    def validate_data(cls, v):
        if isinstance(v, ASRTranscribeResponseSchema):
            return v.model_dump()
        return v