import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AuditLog(models.Model):
    """Immutable append-only audit trail. No update() or delete() allowed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        'accounts.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='audit_logs'
    )
    action = models.CharField(max_length=100)  # e.g. 'ticket.issued', 'payment.succeeded'
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    entity = GenericForeignKey('content_type', 'object_id')
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action', 'created_at'], name='audit_action_time_idx'),
            models.Index(fields=['content_type', 'object_id', 'created_at'], name='audit_entity_idx'),
            models.Index(fields=['actor', 'created_at'], name='audit_actor_time_idx'),
        ]
        # No update or delete — append only
        default_permissions = ('add', 'view')

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('AuditLog entries are immutable and cannot be updated.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('AuditLog entries cannot be deleted.')

    def __str__(self):
        return f'{self.action} by {self.actor} at {self.created_at}'

# retention policy
