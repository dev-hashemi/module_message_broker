"""Multi-part message schema for inter-service communication."""

from typing import Optional
from pydantic import BaseModel

from .message import Message


class SequenceInfo(BaseModel):
    """Information about multi-part message sequences."""
    part_number: int
    total_parts: Optional[int] = None
    is_final: bool = False


class MultipartMessage(Message):
    sequence_info: Optional[SequenceInfo] = None