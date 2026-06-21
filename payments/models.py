import uuid
from django.db import models


class PaymentProvider(models.TextChoices):
    LEMON_SQUEEZY = 'lemon_squeezy', 'LemonSqueezy'
    MPESA = 'mpesa', 'M-Pesa'


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'
    DISPUTED = 'disputed', 'Disputed'


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hold = models.OneToOneField(
        'checkout.CheckoutHold', on_delete=models.PROTECT,
        related_name='payment', null=True, blank=True
    )
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='payments')
    company = models.ForeignKey('companies.Company', on_delete=models.PROTECT, related_name='payments')
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices)
    provider_payment_id = models.CharField(max_length=200, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=200, unique=True, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    provider_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments_payment'
        indexes = [
            models.Index(fields=['company', 'status', 'created_at'], name='payment_company_status_idx'),
            models.Index(fields=['user', 'status'], name='payment_user_status_idx'),
        ]

    def __str__(self):
        return f'{self.provider} {self.provider_payment_id} — {self.amount} {self.currency}'
