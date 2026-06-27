"""
Celery tasks for checkout hold management.

Hold expiry sweep runs every 60 seconds via Celery beat.
Uses Redis sorted set (min-heap) for O(log N + K) expiry detection
instead of O(N) full DB scan.
"""
from celery import shared_task
from django.utils import timezone
from .expiry_heap import pop_expired_holds
from .models import CheckoutHold, HoldStatus
from .hold_registry import release_hold
from inventory.availability_cache import invalidate_availability
import structlog

logger = structlog.get_logger()


@shared_task(name='checkout.sweep_expired_holds')
def sweep_expired_holds():
    """
    Expire all stale checkout holds.

    Algorithm:
      1. Pop expired tokens from Redis sorted set — O(log N + K)
      2. Bulk update DB status to 'expired'
      3. Restore inventory for each expired hold
      4. Remove from O(1) hash map registry

    This runs every 60 seconds via Celery beat.
    """
    expired_tokens = pop_expired_holds()  # O(log N + K)
    if not expired_tokens:
        return {'expired': 0}

    holds = CheckoutHold.objects.filter(
        hold_token__in=expired_tokens,
        status=HoldStatus.ACTIVE,
    ).select_related('tier')

    expired_count = 0
    for hold in holds:
        hold.status = HoldStatus.EXPIRED
        hold.save(update_fields=['status'])
        # Restore inventory
        from inventory.models import TicketTier
        TicketTier.objects.filter(id=hold.tier_id).update(
            quantity_held=hold.tier.quantity_held - hold.quantity
        )
        release_hold(str(hold.hold_token))
        invalidate_availability(str(hold.tier_id))
        expired_count += 1
        logger.info('hold.expired', hold_token=str(hold.hold_token), tier=hold.tier.name)

    return {'expired': expired_count}
