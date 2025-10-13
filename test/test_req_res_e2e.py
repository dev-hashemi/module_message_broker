"""E2E tests for sync request/response messaging."""

import asyncio
import pytest
from module_message_broker import RedisMessageBroker, Message, PubSubTopic
from module_message_broker.schemas.topics import ReqResTopic


class TestSyncRequestResponse:
    """Test sync request/response messaging."""

    @pytest.mark.asyncio
    async def test_simple_request_response(self, client_broker, server_broker):
        """Test basic request/response functionality."""
        
        async def request_handler(request: Message) -> Message:
            user_id = request.data.get("user_id")
            return Message(
                topic=PubSubTopic.LLM_RESPONSE,
                data={"user_id": user_id, "name": f"User {user_id}", "status": "active"}
            )
        
        # Register request handler
        await server_broker.handle_requests([PubSubTopic.LLM_REQUEST], request_handler)
        await asyncio.sleep(0.5)
        
        # Send request
        request = Message(
            topic=PubSubTopic.LLM_REQUEST,
            data={"user_id": "123"}
        )
        
        response = await client_broker.request(request, timeout=5.0)
        
        # Verify response
        assert response.data["user_id"] == "123"
        assert response.data["name"] == "User 123"
        assert response.data["status"] == "active"
        assert response.is_response is True
        assert response.correlation_id is not None

    @pytest.mark.asyncio
    async def test_request_timeout(self, client_broker, server_broker):
        """Test request timeout when no handler is registered."""
        
        # Send request to non-existent topic
        request = Message(
            topic=PubSubTopic.ASR_REQUEST,  # Different topic without handler
            data={"test": "timeout"}
        )
        
        with pytest.raises(TimeoutError):
            await client_broker.request(request, timeout=1.0)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client_broker, server_broker):
        """Test handling multiple concurrent requests."""
        
        async def request_handler(request: Message) -> Message:
            # Simulate some processing time
            await asyncio.sleep(0.1)
            user_id = request.data.get("user_id")
            return Message(
                topic=PubSubTopic.LLM_RESPONSE,
                data={"user_id": user_id, "processed": True}
            )
        
        await server_broker.handle_requests([PubSubTopic.LLM_REQUEST], request_handler)
        await asyncio.sleep(0.5)
        
        # Send multiple concurrent requests
        tasks = []
        for i in range(5):
            request = Message(
                topic=PubSubTopic.LLM_REQUEST,
                data={"user_id": f"user_{i}"}
            )
            tasks.append(client_broker.request(request, timeout=5.0))
        
        responses = await asyncio.gather(*tasks)
        
        # Verify all responses
        assert len(responses) == 5
        for i, response in enumerate(responses):
            assert response.data["user_id"] == f"user_{i}"
            assert response.data["processed"] is True
            assert response.is_response is True

    @pytest.mark.asyncio
    async def test_request_with_complex_data(self, client_broker, server_broker):
        """Test request/response with complex data structures."""
        
        async def request_handler(request: Message) -> Message:
            order_data = request.data.get("order")
            total = sum(item["price"] * item["quantity"] for item in order_data["items"])
            
            return Message(
                topic=PubSubTopic.LLM_REQUEST,
                data={
                    "order_id": order_data["id"],
                    "total": total,
                    "status": "calculated",
                    "items_count": len(order_data["items"])
                }
            )
        
        await server_broker.handle_requests([PubSubTopic.LLM_REQUEST], request_handler)
        await asyncio.sleep(0.5)
        
        # Send request with complex data
        request = Message(
            topic=PubSubTopic.LLM_REQUEST,
            data={
                "order": {
                    "id": "order_123",
                    "items": [
                        {"name": "Item A", "price": 10.99, "quantity": 2},
                        {"name": "Item B", "price": 5.50, "quantity": 1}
                    ]
                }
            }
        )
        
        response = await client_broker.request(request, timeout=5.0)
        
        # Verify response
        assert response.data["order_id"] == "order_123"
        assert response.data["total"] == 27.48  # (10.99 * 2) + (5.50 * 1)
        assert response.data["status"] == "calculated"
        assert response.data["items_count"] == 2

    @pytest.mark.asyncio
    async def test_request_with_error_handling(self, client_broker, server_broker):
        """Test request handler error handling."""
        
        async def failing_request_handler(request: Message) -> Message:
            action = request.data.get("action")
            if action == "fail":
                raise ValueError("Simulated error")
            
            return Message(
                topic=PubSubTopic.LLM_RESPONSE,
                data={"result": "success", "action": action}
            )
        
        await server_broker.handle_requests([PubSubTopic.LLM_REQUEST], failing_request_handler)
        await asyncio.sleep(0.5)
        
        # Send successful request
        success_request = Message(
            topic=PubSubTopic.LLM_REQUEST,
            data={"action": "success"}
        )
        
        response = await client_broker.request(success_request, timeout=5.0)
        assert response.data["result"] == "success"
        assert response.data["action"] == "success"

    @pytest.mark.asyncio
    async def test_multiple_request_handlers(self, redis_client):
        """Test multiple request handlers on different topics."""
        
        client = RedisMessageBroker(redis_client, "multi_client", "client1")
        server1 = RedisMessageBroker(redis_client, "multi_server1", "server1")
        server2 = RedisMessageBroker(redis_client, "multi_server2", "server2")
        
        await client.start_listening()
        await server1.start_listening()
        await server2.start_listening()
        
        try:
            # Handler for LLM_REQUEST
            async def user_handler(request: Message) -> Message:
                return Message(
                    topic=PubSubTopic.LLM_REQUEST,
                    data={"service": "user", "data": request.data}
                )
            
            # Handler for ASR_REQUEST
            async def interaction_handler(request: Message) -> Message:
                return Message(
                    topic=PubSubTopic.ASR_REQUEST,
                    data={"service": "interaction", "data": request.data}
                )
            
            await server1.handle_requests([PubSubTopic.LLM_REQUEST], user_handler)
            await server2.handle_requests([PubSubTopic.ASR_REQUEST], interaction_handler)
            await asyncio.sleep(0.5)
            
            # Send requests to both handlers
            user_request = Message(
                topic=PubSubTopic.LLM_REQUEST,
                data={"type": "user_request"}
            )
            
            interaction_request = Message(
                topic=PubSubTopic.ASR_REQUEST,
                data={"type": "interaction_request"}
            )
            
            user_response = await client.request(user_request, timeout=5.0)
            interaction_response = await client.request(interaction_request, timeout=5.0)
            
            # Verify responses
            assert user_response.data["service"] == "user"
            assert user_response.data["data"]["type"] == "user_request"
            
            assert interaction_response.data["service"] == "interaction"
            assert interaction_response.data["data"]["type"] == "interaction_request"
            
        finally:
            await client.stop_listening()
            await server1.stop_listening()
            await server2.stop_listening()


class TestMixedPatterns:
    """Test combining async pub/sub and sync request/response."""

    @pytest.mark.asyncio
    async def test_async_and_sync_together(self, redis_client):
        """Test using both patterns in the same service."""
        events_received = []
        
        # Create a service that handles both patterns
        service_broker = RedisMessageBroker(redis_client, "mixed_service", "service_1")
        client_broker = RedisMessageBroker(redis_client, "mixed_client", "client_1")
        
        await service_broker.start_listening()
        await client_broker.start_listening()
        
        try:
            # Setup async event handler
            async def event_handler(message: Message):
                events_received.append(message)
            
            await service_broker.subscribe([PubSubTopic.ASR_REQUEST], event_handler)
            
            # Setup sync request handler
            async def request_handler(request: Message) -> Message:
                return Message(
                    topic=PubSubTopic.LLM_REQUEST,
                    data={"echo": request.data, "processed": True}
                )
            
            await service_broker.handle_requests([PubSubTopic.LLM_REQUEST], request_handler)
            await asyncio.sleep(0.5)
            
            # Test async pub/sub
            event = Message(
                topic=PubSubTopic.ASR_REQUEST,
                data={"event": "user_action"}
            )
            await client_broker.publish(event)
            
            # Test sync request/response
            request = Message(
                topic=PubSubTopic.LLM_REQUEST,
                data={"request": "get_data"}
            )
            response = await client_broker.request(request, timeout=5.0)
            
            await asyncio.sleep(1)
            
            # Verify both patterns worked
            assert len(events_received) == 1
            assert events_received[0].data["event"] == "user_action"
            
            assert response.data["echo"]["request"] == "get_data"
            assert response.data["processed"] is True
            
        finally:
            await service_broker.stop_listening()
            await client_broker.stop_listening()

    @pytest.mark.asyncio
    async def test_pub_sub_and_request_response_isolation(self, redis_client):
        """Test that pub/sub and request/response don't interfere with each other."""
        
        # Create separate brokers for different roles
        publisher = RedisMessageBroker(redis_client, "isolation_pub", "pub1")
        subscriber = RedisMessageBroker(redis_client, "isolation_sub", "sub1")
        client = RedisMessageBroker(redis_client, "isolation_client", "client1")
        server = RedisMessageBroker(redis_client, "isolation_server", "server1")
        
        await publisher.start_listening()
        await subscriber.start_listening()
        await client.start_listening()
        await server.start_listening()
        
        try:
            pub_sub_messages = []
            
            # Setup pub/sub
            async def pub_sub_handler(message: Message):
                pub_sub_messages.append(message)
            
            await subscriber.subscribe([PubSubTopic.TTS_REQUEST], pub_sub_handler)
            
            # Setup request/response
            async def request_handler(request: Message) -> Message:
                return Message(
                    topic=ReqResTopic.LLM_GENERATE_TEXT,
                    data={"response_to": request.data}
                )
            
            await server.handle_requests([ReqResTopic.LLM_GENERATE_TEXT], request_handler)
            await asyncio.sleep(0.5)
            
            # Send pub/sub message
            pub_message = Message(
                topic=PubSubTopic.TTS_REQUEST,
                data={"type": "pub_sub", "content": "broadcast"}
            )
            await publisher.publish(pub_message)
            
            # Send request/response
            request_message = Message(
                topic=ReqResTopic.LLM_GENERATE_TEXT,
                data={"type": "request", "content": "query"}
            )
            response = await client.request(request_message, timeout=5.0)
            
            await asyncio.sleep(1)
            
            # Verify both worked independently
            assert len(pub_sub_messages) == 1
            assert pub_sub_messages[0].data["type"] == "pub_sub"
            assert pub_sub_messages[0].data["content"] == "broadcast"
            
            assert response.data["response_to"]["type"] == "request"
            assert response.data["response_to"]["content"] == "query"
            assert response.is_response is True
            
        finally:
            await publisher.stop_listening()
            await subscriber.stop_listening()
            await client.stop_listening()
            await server.stop_listening()