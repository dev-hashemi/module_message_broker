# 🚀 Message Broker Module

Framework-agnostic message broker supporting **async pub/sub** and **sync request/response** patterns with Redis Streams.

## 🚀 Quick Start

```python
import redis.asyncio as redis
from module_message_broker import RedisMessageBroker

# Setup broker - IMPORTANT: decode_responses=True
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
broker = RedisMessageBroker(
    redis_client=redis_client,
    consumer_group="my_service",    # Service name (unique per service)
    consumer_name="instance_1"      # Instance ID (unique per instance)
)

await broker.start_listening()
```

## 📨 Pub/Sub (Events - Fire & Forget)

**Use for:** Events that happened, notifications, loose coupling

```python
from module_message_broker.abstract import UserChatCreateMessage, UserChatCreateSchema

# 📤 Publish Event
message = UserChatCreateMessage(
    data=UserChatCreateSchema(
        user_id="123", question="Hello", answer="Hi!", chat_id="chat_456"
    )
)
await broker.publish(message)

# 📥 Handle Events
async def handle_events(message: Message) -> None:
    print(f"📨 Event: {message.topic} - {message.data}")

await broker.subscribe([PubSubTopic.USER_CHAT_CREATE], handle_events)
```

## 🤝 Request/Response (Commands - RPC Style)

**Use for:** Commands that need responses, synchronous processing

```python
from module_message_broker.abstract import LLMGenerateTextRequestMessage, LLMGenerateTextRequestSchema

# 📞 Make Request
request = LLMGenerateTextRequestMessage(
    data=LLMGenerateTextRequestSchema(
        prompt="Write a haiku about Redis",
        model="gpt-3.5-turbo",
        user_id="123"
    )
)

try:
    response = await broker.request(request, timeout=30.0)
    print(f"🤖 Generated: {response.data.generated_text}")
except TimeoutError:
    print("⏰ Request timed out")

# 🎯 Handle Requests
async def handle_llm_requests(request: Message) -> Message:
    # Process request
    generated_text = f"AI response for: {request.data.prompt}"
    
    return LLMGenerateTextResponseMessage(
        data=LLMGenerateTextResponseSchema(
            success=True,
            generated_text=generated_text,
            tokens_used=50
        )
    )

await broker.handle_requests([RequestTopic.LLM_GENERATE_TEXT], handle_llm_requests)
```

## 🏗️ Service Architecture

```python
# 🤖 LLM Service (handles requests)
broker = RedisMessageBroker(redis_client, "llm_service", "llm_worker_1")
await broker.handle_requests([RequestTopic.LLM_GENERATE_TEXT], handle_llm_requests)

# 👤 User Service (publishes events + makes requests)
broker = RedisMessageBroker(redis_client, "user_service", "user_worker_1") 
await broker.subscribe([PubSubTopic.USER_CHAT_CREATE], handle_user_events)

# Multiple instances share same consumer_group for load balancing
broker1 = RedisMessageBroker(redis_client, "llm_service", "worker_1")
broker2 = RedisMessageBroker(redis_client, "llm_service", "worker_2")
```

## 📋 Available Topics

### PubSubTopic (Events)
- `USER_CHAT_CREATE` - Chat creation events
- `USER_CHAT_INTERACTION_ADD` - Chat interaction events

### RequestTopic (Commands)
- `LLM_GENERATE_TEXT` - Text generation requests
- `LLM_GENERATE_STREAM` - Streaming generation requests  
- `ASR_TRANSCRIBE_AUDIO` - Audio transcription requests
- `TTS_SYNTHESIZE_SPEECH` - Speech synthesis requests

## ⚠️ Important Notes

- **Always set `decode_responses=True`** in Redis client
- **Use different `consumer_group`** for each service type
- **Use unique `consumer_name`** for each instance
- **Handle `TimeoutError`** in request/response calls
- **Call `stop_listening()`** during shutdown

## 🎯 When to Use What

**PubSubTopic:** Events happened, multiple listeners, fire-and-forget  
**RequestTopic:** Need response, direct service communication, RPC-style

## 🔄 Complete Example

```python
async def main():
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # LLM Service
    llm_broker = RedisMessageBroker(redis_client, "llm_service", "llm_1")
    await llm_broker.handle_requests([RequestTopic.LLM_GENERATE_TEXT], handle_llm_requests)
    await llm_broker.start_listening()
    
    # User Service
    user_broker = RedisMessageBroker(redis_client, "user_service", "user_1") 
    await user_broker.start_listening()
    
    # Publish event
    await user_broker.publish(UserChatCreateMessage(...))
    
    # Make request
    response = await user_broker.request(LLMGenerateTextRequestMessage(...))
    
    # Cleanup
    await llm_broker.stop_listening()
    await user_broker.stop_listening()
```