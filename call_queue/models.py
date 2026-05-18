import uuid
from django.db import models
from accounts.models import Organization


class CallQueue(models.Model):

    class Status(models.TextChoices):
        WAITING = 'waiting', 'Waiting'
        CONNECTED = 'connected', 'Connected'
        ABANDONED = 'abandoned', 'Abandoned'
        TIMEOUT = 'timeout', 'Timeout'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='call_queue_entries')

    campaign = models.ForeignKey(
        'campaigns.Campaign',
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )

    caller_number = models.CharField(max_length=20)
    called_number = models.CharField(max_length=20)
    twilio_call_sid = models.CharField(max_length=100)
    twilio_queue_sid = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    position = models.IntegerField(default=0)
    wait_seconds = models.IntegerField(default=0)

    enqueued_at = models.DateTimeField(auto_now_add=True)
    connected_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'call_queue'
        ordering = ['enqueued_at']

    def __str__(self):
        return f"Queue [{self.caller_number}] — {self.status}"