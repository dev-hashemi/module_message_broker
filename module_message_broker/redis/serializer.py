"""Redis message serialization and deserialization."""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict

from ..core.message import Message
from ..core.interfaces import MessageSerializer


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
            "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.now(timezone.utc).isoformat(),
            "is_response": str(message.is_response),
        }

        # Add optional fields
        if message.correlation_id:
            fields["correlation_id"] = message.correlation_id
        if message.reply_to:
            fields["reply_to"] = message.reply_to

        # Add all data fields from the message
        for key, value in message.data.items():
            # Redis streams require string values
            if isinstance(value, (dict, list)):
                fields[f"_type_{key}"] = type(value).__name__
                fields[key] = json.dumps(value)
            elif isinstance(value, (bool, int, float)):
                # Store type information for proper deserialization
                fields[f"_type_{key}"] = type(value).__name__
                fields[key] = str(value)
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
            timestamp = datetime.now(timezone.utc)

        # Parse request/response fields
        correlation_id = data.get("correlation_id") or data.get(b"correlation_id")
        reply_to = data.get("reply_to") or data.get(b"reply_to")
        is_response_val = data.get("is_response") or data.get(b"is_response", b"False")

        # Handle bytes conversion
        if isinstance(correlation_id, bytes):
            correlation_id = correlation_id.decode("utf-8")
        if isinstance(reply_to, bytes):
            reply_to = reply_to.decode("utf-8")
        if isinstance(is_response_val, bytes):
            is_response_val = is_response_val.decode("utf-8")

        is_response = str(is_response_val).lower() == "true"

        # Process all data fields
        reserved_fields = {
            "id",
            "timestamp",
            "correlation_id",
            "reply_to",
            "is_response",
        }
        type_fields = {}
        
        # First pass: collect type information
        for key, value in data.items():
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            if key.startswith("_type_"):
                field_name = key[6:]  # Remove "_type_" prefix
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                type_fields[field_name] = value
        
        # Second pass: process data fields with type conversion
        for key, value in data.items():
            if isinstance(key, bytes):
                key = key.decode("utf-8")
                
            if key not in reserved_fields and not key.startswith("_type_"):
                # Convert bytes to string if needed
                if isinstance(value, bytes):
                    value = value.decode("utf-8")

                # Apply type conversion if type info is available
                if key in type_fields:
                    type_name = type_fields[key]
                    try:
                        if type_name == "bool":
                            message_data[key] = value.lower() == "true"
                        elif type_name == "int":
                            message_data[key] = int(value)
                        elif type_name == "float":
                            message_data[key] = float(value)
                        elif type_name in ("dict", "list"):
                            message_data[key] = json.loads(value)
                        else:
                            message_data[key] = value
                    except (ValueError, AttributeError, json.JSONDecodeError):
                        message_data[key] = value
                else:
                    message_data[key] = value

        return Message(
            topic=topic,
            data=message_data,
            message_id=message_id,
            timestamp=timestamp,
            correlation_id=correlation_id,
            reply_to=reply_to,
            is_response=is_response,
        )
