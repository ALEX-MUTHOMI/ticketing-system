import uuid
from django.db import models


class WebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    provider_event_id = models.CharField(max_length=200, unique=True, db_index=True)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'webhooks_event'
        indexes = [
            models.Index(fields=['provider', 'event_type', 'processed'], name='webhook_provider_type_idx'),
            models.Index(fields=['provider_event_id'], name='webhook_event_id_idx'),
        ]

    def __str__(self):
        return f'{self.provider}:{self.event_type} ({self.provider_event_id})'
