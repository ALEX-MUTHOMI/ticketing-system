import uuid
from django.db import models


class CheckIn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.OneToOneField('tickets.Ticket', on_delete=models.PROTECT, related_name='checkin')
    gate = models.CharField(max_length=100, default='Main')
    scanned_by = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT, related_name='checkins_performed'
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    device_id = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'checkin_checkin'
        indexes = [
            models.Index(fields=['ticket', 'scanned_at'], name='checkin_ticket_time_idx'),
        ]

    def __str__(self):
        return f'CheckIn {self.ticket_id} at {self.gate}'
