"""Redis message serialization and deserialization."""

import json
import uuid
from datetime import datetime
from typing import Dict

from ..abstract import Message, MessageSerializer


class RedisMessageSerializer(MessageSerializer):
    """Redis-specific implementation of MessageSerializer."""
    
    def serialize(self, message: Message) -> Dict[str, str]:
        """Convert Message object to Redis stream entry format.
        
        Args:
            message: Message to serialize
            
        Returns:
            Dictionary with string keys and values for Redis storage
        """
        # Prepare fields for Redis stream
        fields: Dict[str, str] = {
            "id": message.message_id or str(uuid.uuid4()),
            "timestamp": message.timestamp.isoformat(),
        }
        
        # Add all data fields from the message
        for key, value in message.data.items():
            # Redis streams require string values
            if isinstance(value, (dict, list)):
                fields[key] = json.dumps(value)
            elif value is not None:
                fields[key] = str(value)
        
        return fields
    
    def deserialize(self, topic: str, message_id: str, data: Dict[str, str]) -> Message:
        """Convert Redis stream entry to Message object.
        
        Args:
            topic: Message topic (stream name)
            message_id: Redis entry ID
            data: Redis stream entry fields
            
        Returns:
            Deserialized Message object
        """
        message_data = {}
        message_id = data.get("id", message_id)
        
        # Parse timestamp
        timestamp_str = data.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
        except ValueError:
            timestamp = datetime.utcnow()
        
        # Process all data fields
        for key, value in data.items():
            if key not in ("id", "timestamp"):
                # Try to parse JSON values
                try:
                    if value and (value.startswith("{") or value.startswith("[")):
                        message_data[key] = json.loads(value)
                    else:
                        message_data[key] = value
                except (json.JSONDecodeError, AttributeError):
                    message_data[key] = value
        
        return Message(
            topic=topic,
            data=message_data,
            message_id=message_id,
            timestamp=timestamp
        ) 