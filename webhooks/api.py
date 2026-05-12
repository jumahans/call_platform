from ninja import Router
from django.http import HttpRequest
from typing import List
from accounts.api import JWTAuth
from .schemas import (
    CreateWebhookSchema, UpdateWebhookSchema,
    WebhookOutSchema, WebhookDeliveryOutSchema,
    MessageResponseSchema
)
from .services import WebhookService

router = Router(tags=["Webhooks"], auth=JWTAuth())


@router.post("", response={201: WebhookOutSchema, 400: dict})
def create_webhook(request: HttpRequest, data: CreateWebhookSchema):
    try:
        webhook = WebhookService.create(data, request.auth)
        return 201, WebhookService.format(webhook)
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.get("", response={200: List[WebhookOutSchema]})
def list_webhooks(request: HttpRequest):
    webhooks = WebhookService.list(request.auth)
    return 200, [WebhookService.format(w) for w in webhooks]


@router.get("/{webhook_id}", response={200: WebhookOutSchema, 404: dict})
def get_webhook(request: HttpRequest, webhook_id: str):
    try:
        webhook = WebhookService.get(webhook_id, request.auth)
        return 200, WebhookService.format(webhook)
    except ValueError as e:
        return 404, {"detail": str(e)}


@router.patch("/{webhook_id}", response={200: WebhookOutSchema, 400: dict, 404: dict})
def update_webhook(request: HttpRequest, webhook_id: str, data: UpdateWebhookSchema):
    try:
        webhook = WebhookService.update(webhook_id, data, request.auth)
        return 200, WebhookService.format(webhook)
    except ValueError as e:
        return 400, {"detail": str(e)}


@router.delete("/{webhook_id}", response={200: MessageResponseSchema, 404: dict})
def delete_webhook(request: HttpRequest, webhook_id: str):
    try:
        WebhookService.delete(webhook_id, request.auth)
        return 200, {"message": "Webhook deleted successfully", "success": True}
    except ValueError as e:
        return 404, {"detail": str(e)}


@router.get("/{webhook_id}/deliveries", response={200: List[WebhookDeliveryOutSchema], 404: dict})
def list_deliveries(request: HttpRequest, webhook_id: str):
    try:
        deliveries = WebhookService.list_deliveries(webhook_id, request.auth)
        return 200, [
            {
                'id': str(d.id),
                'event': d.event,
                'status': d.status,
                'response_code': d.response_code,
                'response_body': d.response_body,
                'attempts': d.attempts,
                'created_at': d.created_at.isoformat(),
                'updated_at': d.updated_at.isoformat(),
            }
            for d in deliveries
        ]
    except ValueError as e:
        return 404, {"detail": str(e)}


@router.post("/{webhook_id}/test", response={200: dict, 400: dict, 404: dict})
def test_webhook(request: HttpRequest, webhook_id: str):
    try:
        webhook = WebhookService.get(webhook_id, request.auth)
        delivery = WebhookService.deliver(webhook, 'test', {
            'event': 'test',
            'message': 'This is a test webhook delivery',
            'organization_id': str(request.auth.organization_id),
        })
        return 200, {
            'status': delivery.status,
            'response_code': delivery.response_code,
            'response_body': delivery.response_body,
        }
    except ValueError as e:
        return 400, {"detail": str(e)}