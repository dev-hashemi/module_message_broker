"""E2E tests for async pub/sub messaging."""

import asyncio
import pytest
from module_message_broker import RedisMessageBroker, Message, MessageTopic


class TestAsyncPubSub:
    """Test async pub/sub messaging."""

    @pytest.mark.asyncio
    async def test_publish_subscribe_single_message(self, publisher_broker, subscriber_broker):
        """Test publishing and receiving a single message."""
        received_messages = []
        
        async def message_handler(message: Message):
            received_messages.append(message)
        
        # Subscribe to topic
        await subscriber_broker.subscribe([MessageTopic.USER_CHAT_CREATE], message_handler)
        
        # Give time for subscription to be ready
        await asyncio.sleep(0.5)
        
        # Publish message
        test_message = Message(
            topic=MessageTopic.USER_CHAT_CREATE,
            data={"user_id": "123", "action": "test"}
        )
        await publisher_broker.publish(test_message)
        
        # Wait for message processing
        await asyncio.sleep(1)
        
        # Verify message received
        assert len(received_messages) == 1
        assert received_messages[0].data["user_id"] == "123"
        assert received_messages[0].data["action"] == "test"

    @pytest.mark.asyncio
    async def test_publish_subscribe_multiple_messages(self, publisher_broker, subscriber_broker):
        """Test publishing and receiving multiple messages."""
        received_messages = []
        
        async def message_handler(message: Message):
            received_messages.append(message)
        
        await subscriber_broker.subscribe([MessageTopic.USER_CHAT_CREATE], message_handler)
        await asyncio.sleep(0.5)
        
        # Publish multiple messages
        for i in range(3):
            test_message = Message(
                topic=MessageTopic.USER_CHAT_CREATE,
                data={"user_id": f"user_{i}", "index": i}
            )
            await publisher_broker.publish(test_message)
        
        # Wait for all messages to be processed
        await asyncio.sleep(2)
        
        # Verify all messages received
        assert len(received_messages) == 3
        for i, msg in enumerate(received_messages):
            assert msg.data["user_id"] == f"user_{i}"
            assert msg.data["index"] == i

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, publisher_broker, redis_client):
        """Test multiple subscribers receiving the same message."""
        received_messages_1 = []
        received_messages_2 = []
        
        # Create two separate subscriber brokers with unique groups
        sub1 = RedisMessageBroker(redis_client, "test_multi_sub_1", "sub1")
        sub2 = RedisMessageBroker(redis_client, "test_multi_sub_2", "sub2")
        
        await sub1.start_listening()
        await sub2.start_listening()
        
        try:
            async def handler_1(message: Message):
                received_messages_1.append(message)
            
            async def handler_2(message: Message):
                received_messages_2.append(message)
            
            await sub1.subscribe([MessageTopic.USER_CHAT_CREATE], handler_1)
            await sub2.subscribe([MessageTopic.USER_CHAT_CREATE], handler_2)
            await asyncio.sleep(0.5)
            
            # Publish message
            test_message = Message(
                topic=MessageTopic.USER_CHAT_CREATE,
                data={"broadcast": "test"}
            )
            await publisher_broker.publish(test_message)
            
            await asyncio.sleep(1)
            
            # Both subscribers should receive the message
            assert len(received_messages_1) == 1
            assert len(received_messages_2) == 1
            assert received_messages_1[0].data["broadcast"] == "test"
            assert received_messages_2[0].data["broadcast"] == "test"
            
        finally:
            await sub1.stop_listening()
            await sub2.stop_listening()

    @pytest.mark.asyncio
    async def test_unsubscribe(self, publisher_broker, subscriber_broker):
        """Test unsubscribing from topics."""
        received_messages = []
        
        async def message_handler(message: Message):
            received_messages.append(message)
        
        # Subscribe to topic
        await subscriber_broker.subscribe([MessageTopic.USER_CHAT_CREATE], message_handler)
        await asyncio.sleep(0.5)
        
        # Publish first message
        test_message_1 = Message(
            topic=MessageTopic.USER_CHAT_CREATE,
            data={"message": "first"}
        )
        await publisher_broker.publish(test_message_1)
        await asyncio.sleep(1)
        
        # Unsubscribe
        await subscriber_broker.unsubscribe([MessageTopic.USER_CHAT_CREATE])
        await asyncio.sleep(0.5)
        
        # Publish second message (should not be received)
        test_message_2 = Message(
            topic=MessageTopic.USER_CHAT_CREATE,
            data={"message": "second"}
        )
        await publisher_broker.publish(test_message_2)
        await asyncio.sleep(1)
        
        # Should only have received the first message
        assert len(received_messages) == 1
        assert received_messages[0].data["message"] == "first"

    @pytest.mark.asyncio
    async def test_message_with_complex_data(self, publisher_broker, subscriber_broker):
        """Test publishing and receiving messages with complex data structures."""
        received_messages = []
        
        async def message_handler(message: Message):
            received_messages.append(message)
        
        await subscriber_broker.subscribe([MessageTopic.USER_CHAT_CREATE], message_handler)
        await asyncio.sleep(0.5)
        
        # Publish message with complex data
        complex_data = {
            "user": {
                "id": "123",
                "name": "John Doe",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            },
            "items": [
                {"id": 1, "name": "Item 1", "price": 10.99},
                {"id": 2, "name": "Item 2", "price": 15.50}
            ],
            "metadata": {
                "timestamp": "2024-01-01T10:00:00Z",
                "version": 1.2,
                "active": True
            }
        }
        
        test_message = Message(
            topic=MessageTopic.USER_CHAT_CREATE,
            data=complex_data
        )
        await publisher_broker.publish(test_message)
        await asyncio.sleep(1)
        
        # Verify complex data is preserved
        assert len(received_messages) == 1
        msg_data = received_messages[0].data
        
        assert msg_data["user"]["id"] == "123"
        assert msg_data["user"]["name"] == "John Doe"
        assert msg_data["user"]["preferences"]["theme"] == "dark"
        assert msg_data["user"]["preferences"]["notifications"] is True
        assert len(msg_data["items"]) == 2
        assert msg_data["items"][0]["price"] == 10.99
        assert msg_data["metadata"]["version"] == 1.2
        assert msg_data["metadata"]["active"] is True