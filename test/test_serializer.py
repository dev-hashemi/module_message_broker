"""Unit tests for RedisMessageSerializer — no Redis required."""

from datetime import datetime, timezone
from module_message_broker.core.message import Message
from module_message_broker.redis.serializer import RedisMessageSerializer


class TestRedisMessageSerializer:
    """Serializer must not corrupt data during serialization round-trips."""

    def test_string_looking_like_json_remains_string(self):
        """Critical: string values that happen to be valid JSON must not be parsed into dicts."""
        serializer = RedisMessageSerializer()
        msg = Message(topic="test", data={"note": '{"looks": "like json"}'})
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert isinstance(deserialized.data["note"], str)
        assert deserialized.data["note"] == '{"looks": "like json"}'

    def test_string_looking_like_json_array_remains_string(self):
        """String values that look like JSON arrays must not be parsed into lists."""
        serializer = RedisMessageSerializer()
        msg = Message(topic="test", data={"items": '[1, 2, 3]'})
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert isinstance(deserialized.data["items"], str)
        assert deserialized.data["items"] == '[1, 2, 3]'

    def test_empty_json_object_string_remains_string(self):
        """Edge case: '{}' and '[]' strings must not become empty dict/list."""
        serializer = RedisMessageSerializer()
        msg = Message(topic="test", data={"a": '{}', "b": '[]'})
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert isinstance(deserialized.data["a"], str)
        assert deserialized.data["a"] == '{}'
        assert isinstance(deserialized.data["b"], str)
        assert deserialized.data["b"] == '[]'

    def test_dict_round_trips_correctly(self):
        """Actual dict values must round-trip as dicts."""
        serializer = RedisMessageSerializer()
        original = {"nested": {"key": "value"}, "num": 42}
        msg = Message(topic="test", data=original)
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert deserialized.data == original

    def test_list_round_trips_correctly(self):
        """Actual list values must round-trip as lists."""
        serializer = RedisMessageSerializer()
        original = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        msg = Message(topic="test", data={"items": original})
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert deserialized.data["items"] == original

    def test_mixed_types_round_trip(self):
        """Bool, int, float, dict, list, str all round-trip correctly."""
        serializer = RedisMessageSerializer()
        original = {
            "name": "hello",
            "count": 42,
            "price": 10.99,
            "active": True,
            "meta": {"version": 2},
            "tags": ["a", "b"],
        }
        msg = Message(topic="test", data=original)
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert deserialized.data == original

    def test_serialize_with_none_timestamp_does_not_crash(self):
        """Serialization must not crash when timestamp is None."""
        serializer = RedisMessageSerializer()
        msg = Message.model_construct(
            topic="test", data={"key": "val"}, timestamp=None
        )
        serialized = serializer.serialize(msg)
        assert "timestamp" in serialized
        assert serialized["timestamp"] is not None

    def test_serialized_timestamp_is_timezone_aware(self):
        """Serialized timestamp must include timezone info for consistency."""
        serializer = RedisMessageSerializer()
        msg = Message(topic="test", data={"key": "val"})
        serialized = serializer.serialize(msg)
        ts = datetime.fromisoformat(serialized["timestamp"])
        assert ts.tzinfo is not None, (
            f"Expected timezone-aware timestamp, got {serialized['timestamp']}"
        )

    def test_nested_dicts_and_lists_round_trip(self):
        """Deeply nested dicts/lists must round-trip correctly."""
        serializer = RedisMessageSerializer()
        original = {
            "level1": {
                "level2": {
                    "level3": {"value": 42, "items": [1, [2, 3], {"k": "v"}]},
                },
            },
        }
        msg = Message(topic="test", data=original)
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "123", serialized)
        assert deserialized.data == original

    def test_reply_to_and_correlation_id_round_trip(self):
        """Metadata fields (correlation_id, reply_to) must survive round-trip."""
        serializer = RedisMessageSerializer()
        msg = Message(
            topic="test",
            data={"payload": "ok"},
            correlation_id="corr-123",
            reply_to="responses.my-consumer",
            is_response=False,
        )
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "456", serialized)
        assert deserialized.correlation_id == "corr-123"
        assert deserialized.reply_to == "responses.my-consumer"
        assert deserialized.is_response is False

    def test_response_flag_round_trip(self):
        """Response flag must round-trip correctly."""
        serializer = RedisMessageSerializer()
        msg = Message(topic="test", data={}, is_response=True)
        serialized = serializer.serialize(msg)
        deserialized = serializer.deserialize("test", "789", serialized)
        assert deserialized.is_response is True
