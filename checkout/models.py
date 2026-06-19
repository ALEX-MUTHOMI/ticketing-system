import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta


class HoldStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    EXPIRED = 'expired', 'Expired'
    CONFIRMED = 'confirmed', 'Confirmed'
    RELEASED = 'released', 'Released'


class CheckoutHold(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hold_token = models.UUIDField(unique=True, default=uuid.uuid4, db_index=True)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='holds')
    tier = models.ForeignKey('inventory.TicketTier', on_delete=models.CASCADE, related_name='holds')
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=HoldStatus.choices, default=HoldStatus.ACTIVE)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'checkout_hold'
        indexes = [
            models.Index(fields=['status', 'expires_at'], name='hold_status_expiry_idx'),
            models.Index(fields=['user', 'tier', 'status'], name='hold_user_tier_status_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f'Hold {self.hold_token} — {self.tier.name} x{self.quantity}'
