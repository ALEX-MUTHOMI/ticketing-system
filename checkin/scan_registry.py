"""
QR Scan Registry — hash map for O(1) validated-scan lookup.

Problem: Check-in gates receive rapid sequential scans. Each scan
must verify the QR has not already been checked in.

Naive: DB query per scan — O(log N) with index, but still DB latency.

This module maintains a Redis hash map:
  Key: checkin_registry
  Field: qr_fingerprint
  Value: ticket_id (string)

A fingerprint present in the map = already checked in.
Lookup is O(1). Population happens once per scan confirmation.
"""
from django.core.cache import cache

REGISTRY_KEY = 'checkin_registry'
REGISTRY_TTL = 86400  # 24 hours


def is_already_checked_in(qr_fingerprint: str) -> bool:
    """O(1) lookup. Returns True if this QR has already been scanned."""
    client = cache.client.get_client()
    return client.hexists(REGISTRY_KEY, qr_fingerprint)


def register_checkin(qr_fingerprint: str, ticket_id: str) -> None:
    """Record a successful check-in. O(1) Redis hset."""
    client = cache.client.get_client()
    client.hset(REGISTRY_KEY, qr_fingerprint, ticket_id)
    client.expire(REGISTRY_KEY, REGISTRY_TTL)


def get_ticket_id_for_qr(qr_fingerprint: str) -> str | None:
    """Resolve ticket_id from fingerprint. O(1)."""
    client = cache.client.get_client()
    value = client.hget(REGISTRY_KEY, qr_fingerprint)
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else value
