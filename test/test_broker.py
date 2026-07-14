"""Unit tests for RedisMessageBroker — no Redis required."""

from unittest.mock import MagicMock
from module_message_broker import RedisMessageBroker


class TestRedisMessageBroker:
    """Broker initialization and component wiring."""

    def test_consumer_and_reqres_have_distinct_consumer_names(self):
        """Consumer and request-response must use different consumer names
        to avoid identity collision in the same consumer group.
        """
        redis_mock = MagicMock()
        broker = RedisMessageBroker(
            redis_client=redis_mock,
            consumer_group="test_group",
            consumer_name="my_instance",
        )
        consumer_name = broker._consumer._consumer_name
        reqres_name = broker._request_response._consumer_name
        assert consumer_name != reqres_name, (
            f"Consumer and req-res must not share the same name: "
            f"consumer={consumer_name}, reqres={reqres_name}"
        )
        assert reqres_name == f"{consumer_name}-reqres", (
            f"Expected req-res name to be '{consumer_name}-reqres', "
            f"got '{reqres_name}'"
        )

    def test_consumer_and_reqres_share_consumer_group(self):
        """Both components should belong to the same consumer group."""
        redis_mock = MagicMock()
        broker = RedisMessageBroker(
            redis_client=redis_mock,
            consumer_group="shared_group",
        )
        assert broker._consumer._consumer_group == "shared_group"
        assert broker._request_response._consumer_group == "shared_group"

    def test_auto_generated_consumer_names_also_distinct(self):
        """When consumer_name is not provided, names must still be distinct."""
        redis_mock = MagicMock()
        broker = RedisMessageBroker(
            redis_client=redis_mock,
            consumer_group="auto_group",
        )
        consumer_name = broker._consumer._consumer_name
        reqres_name = broker._request_response._consumer_name
        assert consumer_name != reqres_name
        assert reqres_name == f"{consumer_name}-reqres"
        assert consumer_name.startswith("consumer-")
