import uuid
from django.db import models
from django.utils import timezone


class TicketTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='tiers')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    quantity_total = models.PositiveIntegerField()
    quantity_held = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    max_per_order = models.PositiveIntegerField(default=10)
    sale_starts_at = models.DateTimeField(null=True, blank=True)
    sale_ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_tier'
        ordering = ['sort_order', 'price']
        indexes = [
            models.Index(fields=['event', 'is_active'], name='tier_event_active_idx'),
            models.Index(fields=['event', 'price'], name='tier_event_price_idx'),
        ]

    def __str__(self):
        return f'{self.name} — {self.price} {self.currency}'

    @property
    def quantity_available(self):
        """Available = total - held - sold. No Python-side scan."""
        return max(0, self.quantity_total - self.quantity_held - self.quantity_sold)

    def is_on_sale(self):
        now = timezone.now()
        if self.sale_starts_at and now < self.sale_starts_at:
            return False
        if self.sale_ends_at and now > self.sale_ends_at:
            return False
        return self.is_active and self.quantity_available > 0
