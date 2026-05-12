from ninja import Schema
from typing import Optional, List


class CreateWebhookSchema(Schema):
    name: str
    url: str
    secret: Optional[str] = ''
    events: List[str] = []
    max_retries: Optional[int] = 3
    timeout_seconds: Optional[int] = 10


class UpdateWebhookSchema(Schema):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    status: Optional[str] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None


class WebhookDeliveryOutSchema(Schema):
    id: str
    event: str
    status: str
    response_code: Optional[int] = None
    response_body: str
    attempts: int
    created_at: str
    updated_at: str


class WebhookOutSchema(Schema):
    id: str
    name: str
    url: str
    events: list
    status: str
    max_retries: int
    timeout_seconds: int
    organization_id: str
    created_at: str
    updated_at: str


class MessageResponseSchema(Schema):
    message: str
    success: bool = True