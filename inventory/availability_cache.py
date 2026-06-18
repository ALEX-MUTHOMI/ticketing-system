"""
Availability cache with TTL invalidation.

Caches tier quantity_available values in Redis.
Invalidated on every hold creation, hold release, and ticket issue.

This prevents repeated DB annotation queries on the hot availability path.
"""
from django.core.cache import cache

AVAILABILITY_PREFIX = 'tier_avail:'
AVAILABILITY_TTL = 30  # 30 seconds — short TTL for accuracy


def get_cached_availability(tier_id: str) -> int | None:
    return cache.get(f'{AVAILABILITY_PREFIX}{tier_id}')


def set_cached_availability(tier_id: str, quantity: int) -> None:
    cache.set(f'{AVAILABILITY_PREFIX}{tier_id}', quantity, AVAILABILITY_TTL)


def invalidate_availability(tier_id: str) -> None:
    cache.delete(f'{AVAILABILITY_PREFIX}{tier_id}')
