import uuid
from django.db import models
from accounts.models import Organization, User


class NotificationRule(models.Model):

    class Channel(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'

    class Event(models.TextChoices):
        CALL_MISSED = 'call.missed', 'Call Missed'
        CALL_COMPLETED = 'call.completed', 'Call Completed'
        CAMPAIGN_CAP_REACHED = 'campaign.cap_reached', 'Campaign Cap Reached'
        BUYER_CAP_REACHED = 'buyer.cap_reached', 'Buyer Cap Reached'
        PUBLISHER_CAP_REACHED = 'publisher.cap_reached', 'Publisher Cap Reached'
        LOW_BALANCE = 'low.balance', 'Low Balance'
        CAMPAIGN_PAUSED = 'campaign.paused', 'Campaign Paused'
        DAILY_SUMMARY = 'daily.summary', 'Daily Summary'
        NEW_CALL = 'call.started', 'New Call'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notification_rules')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_notification_rules')

    name = models.CharField(max_length=255)
    event = models.CharField(max_length=50, choices=Event.choices)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.EMAIL)
    recipients = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_rules'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.event})"


class NotificationLog(models.Model):

    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        PENDING = 'pending', 'Pending'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='notification_logs')
    rule = models.ForeignKey(NotificationRule, on_delete=models.SET_NULL, null=True, related_name='logs')

    event = models.CharField(max_length=50)
    channel = models.CharField(max_length=20)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event} → {self.recipient} ({self.status})"