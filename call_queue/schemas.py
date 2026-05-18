from ninja import Schema
from typing import Optional
from datetime import datetime


class CallQueueOutSchema(Schema):
    id: str
    caller_number: str
    called_number: str
    campaign_id: str
    campaign_name: str
    status: str
    position: int
    wait_seconds: int
    enqueued_at: str


class MessageResponseSchema(Schema):
    message: str
    success: bool = True