"""Core message data structure for inter-service communication."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator


class Message(BaseModel):
    """Message data structure for inter-service communication.
    
    This class is a Pydantic model that defines the structure of a message.
    It can be used as a base class for concrete message classes or instantiated directly.
    """

    topic: str  # Only string type allowed for topic
    data: Dict[str, Any]
    message_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    is_response: bool = False

    @model_validator(mode='before')
    @classmethod
    def set_default_timestamp(cls, values):
        """Set default timestamp if not provided."""
        if isinstance(values, dict):
            if values.get('timestamp') is None:
                values['timestamp'] = datetime.now(timezone.utc)
        return values