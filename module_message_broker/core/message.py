"""Core message data structure for inter-service communication."""

import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union


@dataclass
class Message(abc.ABC):
    """Message data structure for inter-service communication.
    
    This class is an abstract base class that defines the structure of a message.
    It is not intended to be instantiated directly, but rather to be used as a base
    class for concrete message classes.
    """

    topic: Union[str, Any]  # Can be string or topic enum
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