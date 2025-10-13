"""User service message schemas."""

from typing import Optional
from pydantic import BaseModel, field_validator

from ..core.message import Message
from .topics import PubSubTopic


class UserDeletedEventSchema(BaseModel):
    """Schema for user deletion events."""
    user_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    deleted_at: Optional[str] = None


class UserDeletedEventMessage(Message):
    """User soft deleted event message for pub/sub."""
    topic: PubSubTopic = PubSubTopic.USER_SOFT_DELETED
    
    @field_validator('data', mode='before')
    @classmethod
    def validate_data(cls, v):
        if isinstance(v, UserDeletedEventSchema):
            return v.model_dump()
        return v
