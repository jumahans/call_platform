from ninja import Schema
from typing import Optional, List


class CreateNotificationRuleSchema(Schema):
    name: str
    event: str
    channel: str = 'email'
    recipients: List[str] = []
    is_active: bool = True


class UpdateNotificationRuleSchema(Schema):
    name: Optional[str] = None
    event: Optional[str] = None
    channel: Optional[str] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[bool] = None


class NotificationRuleOutSchema(Schema):
    id: str
    name: str
    event: str
    channel: str
    recipients: list
    is_active: bool
    organization_id: str
    created_at: str
    updated_at: str


class NotificationLogOutSchema(Schema):
    id: str
    event: str
    channel: str
    recipient: str
    subject: str
    status: str
    error: str
    created_at: str


class MessageResponseSchema(Schema):
    message: str
    success: bool = True