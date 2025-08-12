"""Redis message serialization and deserialization."""

import json
import uuid
from datetime import datetime
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
            "timestamp": message.timestamp.isoformat(),
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
        for key, value in data.items():
            if key not in reserved_fields:
                # Convert bytes to string if needed
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                if isinstance(key, bytes):
                    key = key.decode("utf-8")

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
            timestamp=timestamp,
            correlation_id=correlation_id,
            reply_to=reply_to,
            is_response=is_response,
        )
