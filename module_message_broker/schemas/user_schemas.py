"""User service message schemas."""

from pydantic import BaseModel

from ..core.message import Message
from .topics import PubSubTopic


class UserChatCreateSchema(BaseModel):
    """Schema for user chat creation events."""
    user_id: str
    question: str
    answer: str
    chat_id: str


class UserChatInteractionAddSchema(BaseModel):
    """Schema for user chat interaction events."""
    user_id: str
    question: str
    answer: str
    chat_id: str


class UserChatCreateMessage(Message):
    """User chat create message."""
    topic: PubSubTopic = PubSubTopic.USER_CHAT_CREATE
    data: UserChatCreateSchema


class UserChatInteractionAddMessage(Message):
    """User chat interaction add message."""
    topic: PubSubTopic = PubSubTopic.USER_CHAT_INTERACTION_ADD
    data: UserChatInteractionAddSchema