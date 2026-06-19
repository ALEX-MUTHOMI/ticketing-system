"""
Min-heap hold expiry scheduler.

Problem: The Celery sweep task must find all expired holds efficiently.
Naive DB query: `CheckoutHold.objects.filter(expires_at__lt=now)` — O(N)
full scan if no index, O(log N) with index but still a DB round-trip.

This module uses a Redis sorted set as a distributed min-heap:
  - Score = Unix timestamp of expires_at
  - Member = hold_token (string)

Celery beat calls `pop_expired_holds()` every 60 seconds:
  ZRANGEBYSCORE key 0 <now_timestamp> — O(log N + K) where K = expired count

Time complexity:
  push:   O(log N) — sorted set insert
  pop_expired: O(log N + K) — range query + remove

This is far more efficient than a full DB scan on large hold volumes.
"""
import time
from django.core.cache import cache

HOLD_EXPIRY_ZSET = 'hold_expiry_zset'


def push_hold_expiry(hold_token: str, expires_at_timestamp: float) -> None:
    """Register a hold for expiry tracking. O(log N)."""
    client = cache.client.get_client()
    client.zadd(HOLD_EXPIRY_ZSET, {hold_token: expires_at_timestamp})


def pop_expired_holds() -> list[str]:
    """
    Return and remove all hold tokens that have expired.
    O(log N + K) where K is the number of expired holds.
    """
    now = time.time()
    client = cache.client.get_client()
    pipeline = client.pipeline()
    pipeline.zrangebyscore(HOLD_EXPIRY_ZSET, 0, now)
    pipeline.zremrangebyscore(HOLD_EXPIRY_ZSET, 0, now)
    results = pipeline.execute()
    expired_tokens = results[0]
    return [t.decode() if isinstance(t, bytes) else t for t in expired_tokens]


def remove_from_expiry_set(hold_token: str) -> None:
    """Remove a confirmed/released hold from the expiry set. O(log N)."""
    client = cache.client.get_client()
    client.zrem(HOLD_EXPIRY_ZSET, hold_token)
