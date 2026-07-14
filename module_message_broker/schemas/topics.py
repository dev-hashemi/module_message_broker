"""Message topics for inter-service communication."""

from enum import Enum


class PubSubTopic(str, Enum):
    """Pub/Sub message topics for asynchronous event-driven communication."""

    # Service communication topics
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    
    # User service events
    USER_SOFT_DELETED = "user.soft_deleted"
    USER_CREATED = "user.created"

    # Subscription service events
    SUBSCRIPTION_UPDATED = "subscription.updated"

    # Notification events
    NOTIFICATION_SEND = "notification.send"
    NOTIFICATION_NOTIFY = "notification.notify"
    NOTIFICATION_BROADCAST = "notification.broadcast"
    NOTIFICATION_INBOX_MARK_READ = "notification.inbox.mark_read"
    NOTIFICATION_PREFERENCES_UPDATE = "notification.preferences.update"
    NOTIFICATION_TEMPLATES_CREATE = "notification.templates.create"
    NOTIFICATION_TEMPLATES_UPDATE = "notification.templates.update"
    NOTIFICATION_TEMPLATES_DELETE = "notification.templates.delete"


class ReqResTopic(str, Enum):
    """Request/Response topics for synchronous inter-service communication."""

    # LLM service requests
    LLM_GENERATE_TEXT = "llm.generate.text"

    # Notification requests
    NOTIFICATION_INBOX_LIST = "notification.inbox.list"
    NOTIFICATION_PREFERENCES_GET = "notification.preferences.get"
    NOTIFICATION_TEMPLATES_LIST = "notification.templates.list"
    NOTIFICATION_TEMPLATES_GET = "notification.templates.get"


