"""
Idempotency store for payment deduplication.

Problem: Payment webhooks are delivered at-least-once. LemonSqueezy and
M-Pesa may retry the same event multiple times. Without deduplication,
each retry would issue a duplicate ticket.

Solution: Hash map of processed payment IDs.
  Key: provider_payment_id or webhook event_id
  Value: Result dict (ticket_id, status)

Time complexity: O(1) get/set.
Security: Without this, a replay attack on the webhook endpoint would
issue unlimited tickets for a single payment.
"""
import json
from django.core.cache import cache

IDEM_PREFIX = 'idem:payment:'
IDEM_TTL = 86400 * 7  # 7 days


def is_processed(payment_id: str) -> bool:
    """Check if payment_id has already been processed. O(1)."""
    return cache.get(f'{IDEM_PREFIX}{payment_id}') is not None


def mark_processed(payment_id: str, result: dict) -> None:
    """Record a processed payment. O(1)."""
    cache.set(f'{IDEM_PREFIX}{payment_id}', json.dumps(result), IDEM_TTL)


def get_result(payment_id: str) -> dict | None:
    """Return cached result for a payment. Used to return idempotent response."""
    data = cache.get(f'{IDEM_PREFIX}{payment_id}')
    if data is None:
        return None
    return json.loads(data)
