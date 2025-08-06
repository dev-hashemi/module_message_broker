# 🚀 Message Broker Module

Framework-agnostic message broker supporting **async pub/sub** and **sync request/response** patterns.

## 🚀 Quick Start

```python
import redis.asyncio as redis
from module_message_broker import RedisMessageBroker, Message, MessageTopic

# 🔧 Setup broker
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)
broker = RedisMessageBroker(
    redis_client=redis_client,
    consumer_group="my_service",    # 🏷️ Service name
    consumer_name="instance_1"      # 🆔 Instance ID
)

await broker.start_listening()
```

## 📨 Async Pub/Sub (Fire & Forget)

### 📤 Publishing Events

```python
# 🚀 Publish event
message = Message(
    topic=MessageTopic.USER_CHAT_CREATE,
    data={"user_id": "123", "action": "created"}
)
await broker.publish(message)
```

### 📥 Handling Events

```python
# 🎯 Event handler
async def handle_events(message: Message) -> None:
    print(f"📨 Event: {message.data}")
    # Process event...

# 🔗 Subscribe
await broker.subscribe([MessageTopic.USER_CHAT_CREATE], handle_events)
```

## 🤝 Sync Request/Response (RPC Style)

### 📞 Making Requests

```python
# 🔍 Send request
request = Message(
    topic=MessageTopic.USER_CHAT_CREATE,
    data={"user_id": "123", "action": "get_profile"}
)

try:
    response = await broker.request(request, timeout=10.0)
    print(f"👤 Response: {response.data}")
except TimeoutError:
    print("⏰ Request timed out")
```

### 🎯 Handling Requests

```python
# 🛠️ Request handler
async def handle_requests(request: Message) -> Message:
    user_id = request.data.get("user_id")
    
    # Process request and return response
    return Message(
        topic=MessageTopic.USER_CHAT_CREATE,
        data={"user_id": user_id, "name": f"User {user_id}"}
    )

# 🔗 Register handler
await broker.handle_requests([MessageTopic.USER_CHAT_CREATE], handle_requests)
```

## ⚙️ Configuration

### 🔧 Broker Setup

```python
# 🏠 Local development
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)

# ☁️ Production
redis_client = redis.Redis(
    host='redis.example.com',
    port=6379,
    password='your_password',
    decode_responses=False,  # ⚠️ Must be False
    max_connections=20
)

broker = RedisMessageBroker(
    redis_client=redis_client,
    consumer_group="my_service",     # Different per service
    consumer_name="worker_1"         # Unique per instance
)
```

## 🔄 Complete Example

```python
import asyncio
import redis.asyncio as redis
from module_message_broker import RedisMessageBroker, Message, MessageTopic

async def main():
    # Setup
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=False)
    broker = RedisMessageBroker(redis_client, "my_service", "worker_1")
    await broker.start_listening()
    
    # Async pub/sub
    async def handle_events(message: Message):
        print(f"📨 Event: {message.data}")
    
    await broker.subscribe([MessageTopic.USER_CHAT_CREATE], handle_events)
    
    # Sync request/response
    async def handle_requests(request: Message) -> Message:
        return Message(
            topic=MessageTopic.USER_CHAT_CREATE,
            data={"result": "processed", "input": request.data}
        )
    
    await broker.handle_requests([MessageTopic.USER_CHAT_CREATE], handle_requests)
    
    # Test both patterns
    await broker.publish(Message(topic=MessageTopic.USER_CHAT_CREATE, data={"test": "event"}))
    
    response = await broker.request(
        Message(topic=MessageTopic.USER_CHAT_CREATE, data={"test": "request"}),
        timeout=5.0
    )
    print(f"Response: {response.data}")
    
    # Cleanup
    await broker.stop_listening()
    await redis_client.aclose()

asyncio.run(main())
```

## ⚠️ Important Notes

- **Always set `decode_responses=False`** in Redis client
- **Use different `consumer_group`** for each service
- **Use unique `consumer_name`** for each instance
- **Always call `stop_listening()`** when shutting down
- **Handle `TimeoutError`** in request/response calls