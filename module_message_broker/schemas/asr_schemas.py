"""ASR service message schemas."""

from typing import Optional
from pydantic import BaseModel

from ..core.message import Message
from .topics import RequestTopic


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
    topic: RequestTopic = RequestTopic.ASR_TRANSCRIBE_AUDIO
    data: ASRTranscribeRequestSchema


class ASRTranscribeResponseMessage(Message):
    """ASR transcribe response message."""
    topic: RequestTopic = RequestTopic.ASR_TRANSCRIBE_AUDIO
    data: ASRTranscribeResponseSchema
    is_response: bool = True