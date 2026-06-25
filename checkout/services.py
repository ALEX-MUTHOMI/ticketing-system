"""
Checkout hold services.

Business logic for creating, confirming, and releasing checkout holds.
All inventory mutations use SELECT FOR UPDATE to prevent race conditions
on the last available ticket.

Security:
  - Max 2 active holds per user per event (hold abuse guard)
  - Sliding window rate limit applied at API layer
  - SELECT FOR UPDATE prevents oversell under concurrency
"""
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import CheckoutHold, HoldStatus
from .hold_registry import HoldEntry, register_hold, release_hold
from .expiry_heap import push_hold_expiry
from inventory.models import TicketTier
from inventory.availability_cache import invalidate_availability


MAX_HOLDS_PER_USER_PER_EVENT = 2
HOLD_DURATION_MINUTES = 15


class HoldError(Exception):
    pass


class HoldAbuseError(HoldError):
    pass


class InsufficientInventoryError(HoldError):
    pass


@transaction.atomic
def create_hold(user, tier_id: str, quantity: int) -> CheckoutHold:
    """
    Create a checkout hold with inventory lock.

    Uses SELECT FOR UPDATE to prevent race condition on last ticket.
    Enforces max hold abuse guard (MAX 2 active holds/user/event).

    Raises:
        HoldAbuseError: User already has too many active holds for this event.
        InsufficientInventoryError: Not enough tickets available.
    """
    # Lock the tier row — prevents concurrent oversell
    tier = TicketTier.objects.select_for_update().get(id=tier_id)

    # Abuse guard: count active holds for this user on this event
    active_holds_count = CheckoutHold.objects.filter(
        user=user,
        tier__event=tier.event,
        status=HoldStatus.ACTIVE,
    ).count()
    if active_holds_count >= MAX_HOLDS_PER_USER_PER_EVENT:
        raise HoldAbuseError(
            f'Maximum {MAX_HOLDS_PER_USER_PER_EVENT} active holds per event. Release existing holds first.'
        )

    if tier.quantity_available < quantity:
        raise InsufficientInventoryError(
            f'Only {tier.quantity_available} tickets available, {quantity} requested.'
        )

    expires_at = timezone.now() + timedelta(minutes=HOLD_DURATION_MINUTES)
    hold = CheckoutHold.objects.create(
        user=user, tier=tier, quantity=quantity, expires_at=expires_at
    )

    # Increment held quantity
    TicketTier.objects.filter(id=tier_id).update(
        quantity_held=tier.quantity_held + quantity
    )

    # Register in O(1) hash map
    entry = HoldEntry(
        tier_id=str(tier_id),
        quantity=quantity,
        expires_at=expires_at,
        user_id=str(user.id)
    )
    register_hold(str(hold.hold_token), entry)
    # Register in min-heap for expiry sweep
    push_hold_expiry(str(hold.hold_token), expires_at.timestamp())
    # Invalidate availability cache
    invalidate_availability(str(tier_id))

    return hold


@transaction.atomic
def release_hold_by_token(hold_token: str) -> None:
    """Release a hold and restore inventory."""
    try:
        hold = CheckoutHold.objects.select_for_update().get(
            hold_token=hold_token, status=HoldStatus.ACTIVE
        )
    except CheckoutHold.DoesNotExist:
        return

    hold.status = HoldStatus.RELEASED
    hold.save(update_fields=['status'])

    TicketTier.objects.filter(id=hold.tier_id).update(
        quantity_held=hold.tier.quantity_held - hold.quantity
    )
    release_hold(hold_token)
    invalidate_availability(str(hold.tier_id))
