import hmac
import hashlib
import json
import httpx
from datetime import timedelta
from django.utils import timezone
from .models import Webhook, WebhookDelivery
from accounts.models import User


class WebhookService:

    @staticmethod
    def create(data, user: User) -> Webhook:
        if not user.organization:
            raise ValueError("User has no organization")

        webhook = Webhook.objects.create(
            organization=user.organization,
            created_by=user,
            name=data.name,
            url=data.url,
            secret=data.secret or '',
            events=data.events or [],
            max_retries=data.max_retries or 3,
            timeout_seconds=data.timeout_seconds or 10,
            status=Webhook.Status.ACTIVE
        )
        return webhook

    @staticmethod
    def get(webhook_id: str, user: User) -> Webhook:
        try:
            return Webhook.objects.get(
                id=webhook_id,
                organization=user.organization
            )
        except Webhook.DoesNotExist:
            raise ValueError("Webhook not found")

    @staticmethod
    def list(user: User):
        return Webhook.objects.filter(
            organization=user.organization
        ).order_by('-created_at')

    @staticmethod
    def update(webhook_id: str, data, user: User) -> Webhook:
        webhook = WebhookService.get(webhook_id, user)

        fields = ['name', 'url', 'secret', 'events', 'status', 'max_retries', 'timeout_seconds']
        for field in fields:
            value = getattr(data, field, None)
            if value is not None:
                setattr(webhook, field, value)

        webhook.save()
        return webhook

    @staticmethod
    def delete(webhook_id: str, user: User):
        webhook = WebhookService.get(webhook_id, user)
        webhook.delete()

    @staticmethod
    def deliver(webhook: Webhook, event: str, payload: dict):
        delivery = WebhookDelivery.objects.create(
            webhook=webhook,
            event=event,
            payload=payload,
            status=WebhookDelivery.Status.PENDING
        )
        WebhookService._send(delivery)
        return delivery

    @staticmethod
    def _send(delivery: WebhookDelivery):
        webhook = delivery.webhook
        payload_str = json.dumps(delivery.payload)

        headers = {'Content-Type': 'application/json'}

        if webhook.secret:
            signature = hmac.new(
                webhook.secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f"sha256={signature}"

        try:
            response = httpx.post(
                webhook.url,
                content=payload_str,
                headers=headers,
                timeout=webhook.timeout_seconds
            )
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:500]
            delivery.attempts += 1

            if response.status_code in [200, 201, 202, 204]:
                delivery.status = WebhookDelivery.Status.SUCCESS
            else:
                delivery.status = WebhookDelivery.Status.FAILED
                if delivery.attempts < webhook.max_retries:
                    delivery.status = WebhookDelivery.Status.RETRYING
                    delivery.next_retry_at = timezone.now() + timedelta(minutes=5)

        except Exception as e:
            delivery.attempts += 1
            delivery.response_body = str(e)[:500]
            delivery.status = WebhookDelivery.Status.FAILED
            if delivery.attempts < webhook.max_retries:
                delivery.status = WebhookDelivery.Status.RETRYING
                delivery.next_retry_at = timezone.now() + timedelta(minutes=5)

        delivery.save()

    @staticmethod
    def dispatch(organization_id: str, event: str, payload: dict):
        webhooks = Webhook.objects.filter(
            organization_id=organization_id,
            status=Webhook.Status.ACTIVE
        )
        for webhook in webhooks:
            if event in webhook.events or '*' in webhook.events:
                WebhookService.deliver(webhook, event, payload)

    @staticmethod
    def list_deliveries(webhook_id: str, user: User):
        webhook = WebhookService.get(webhook_id, user)
        return WebhookDelivery.objects.filter(
            webhook=webhook
        ).order_by('-created_at')[:100]

    @staticmethod
    def format(webhook: Webhook) -> dict:
        return {
            'id': str(webhook.id),
            'name': webhook.name,
            'url': webhook.url,
            'events': webhook.events,
            'status': webhook.status,
            'max_retries': webhook.max_retries,
            'timeout_seconds': webhook.timeout_seconds,
            'organization_id': str(webhook.organization_id),
            'created_at': webhook.created_at.isoformat(),
            'updated_at': webhook.updated_at.isoformat(),
        }