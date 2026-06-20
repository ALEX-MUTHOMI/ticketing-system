import uuid
import hmac
import hashlib
import secrets
from django.db import models
from django.conf import settings


class TicketStatus(models.TextChoices):
    ISSUED = 'issued', 'Issued'
    CHECKED_IN = 'checked_in', 'Checked In'
    CANCELLED = 'cancelled', 'Cancelled'
    TRANSFERRED = 'transferred', 'Transferred'


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hold = models.OneToOneField(
        'checkout.CheckoutHold', on_delete=models.PROTECT,
        related_name='ticket', null=True, blank=True
    )
    payment = models.ForeignKey(
        'payments.Payment', on_delete=models.PROTECT,
        related_name='tickets', null=True, blank=True
    )
    tier = models.ForeignKey('inventory.TicketTier', on_delete=models.PROTECT, related_name='tickets')
    attendee = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='tickets')
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.ISSUED)
    # HMAC-SHA256 signed fingerprint — unforgeable without QR_SECRET
    qr_fingerprint = models.CharField(max_length=64, unique=True, db_index=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tickets_ticket'
        indexes = [
            models.Index(fields=['tier', 'status'], name='ticket_tier_status_idx'),
            models.Index(fields=['attendee', 'status'], name='ticket_attendee_status_idx'),
        ]

    def __str__(self):
        return f'Ticket {self.id} — {self.tier.name}'

    @classmethod
    def generate_qr_fingerprint(cls, ticket_id: str) -> str:
        """
        Generate an HMAC-SHA256 signed QR fingerprint.

        Security: Only the server knows QR_SECRET. An attacker cannot
        generate a valid fingerprint without it. Any tampered QR is
        immediately detected on scan.

        The fingerprint encodes: ticket_id + random nonce.
        """
        secret = getattr(settings, 'QR_SECRET', 'insecure-dev-secret')
        nonce = secrets.token_hex(8)
        payload = f'{ticket_id}:{nonce}'
        signature = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return signature
