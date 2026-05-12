import uuid
from django.db import models
from accounts.models import Organization, User


class Webhook(models.Model):

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PAUSED = 'paused', 'Paused'

    class Event(models.TextChoices):
        CALL_STARTED = 'call.started', 'Call Started'
        CALL_COMPLETED = 'call.completed', 'Call Completed'
        CALL_FAILED = 'call.failed', 'Call Failed'
        CALL_NO_ANSWER = 'call.no_answer', 'Call No Answer'
        CALL_CONVERTED = 'call.converted', 'Call Converted'
        RTB_AUCTION_CREATED = 'rtb.auction_created', 'RTB Auction Created'
        RTB_AUCTION_CLOSED = 'rtb.auction_closed', 'RTB Auction Closed'
        CAMPAIGN_PAUSED = 'campaign.paused', 'Campaign Paused'
        CAMPAIGN_CAP_REACHED = 'campaign.cap_reached', 'Campaign Cap Reached'
        BUYER_CAP_REACHED = 'buyer.cap_reached', 'Buyer Cap Reached'
        PUBLISHER_CAP_REACHED = 'publisher.cap_reached', 'Publisher Cap Reached'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='webhooks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_webhooks')

    name = models.CharField(max_length=255)
    url = models.URLField()
    secret = models.CharField(max_length=255, blank=True)
    events = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Retry settings
    max_retries = models.IntegerField(default=3)
    timeout_seconds = models.IntegerField(default=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhooks'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.url})"


class WebhookDelivery(models.Model):

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        RETRYING = 'retrying', 'Retrying'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')

    event = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    response_code = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    attempts = models.IntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} → {self.webhook.url} ({self.status})"