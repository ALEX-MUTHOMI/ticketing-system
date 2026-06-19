"""
Hash-map based hold registry for O(1) hold lookup.

Problem: Every checkout confirmation must verify the hold is still active
and not expired. Hitting the DB on every confirmation under high concurrency
creates contention.

Solution: An in-process hash map (dict) backed by Redis for O(1) lookup
by hold_token. The DB is the source of truth; this is a read cache.

Time complexity: O(1) get/set/delete.
Space complexity: O(H) where H is active holds.

Security note: The hash map stores only non-sensitive metadata
(tier_id, quantity, expires_at). The full hold is always confirmed in DB
before any mutation.
"""
import json
from datetime import datetime
from django.core.cache import cache

HOLD_PREFIX = 'hold:'
HOLD_TTL_BUFFER = 60  # extra seconds beyond hold expiry


class HoldEntry:
    __slots__ = ('tier_id', 'quantity', 'expires_at', 'user_id')

    def __init__(self, tier_id: str, quantity: int, expires_at: datetime, user_id: str):
        self.tier_id = tier_id
        self.quantity = quantity
        self.expires_at = expires_at
        self.user_id = user_id

    def to_dict(self):
        return {
            'tier_id': self.tier_id,
            'quantity': self.quantity,
            'expires_at': self.expires_at.isoformat(),
            'user_id': self.user_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            tier_id=data['tier_id'],
            quantity=data['quantity'],
            expires_at=datetime.fromisoformat(data['expires_at']),
            user_id=data['user_id'],
        )


def register_hold(hold_token: str, entry: HoldEntry) -> None:
    """Add hold to registry. O(1) Redis set."""
    from django.utils import timezone
    ttl = max(1, int((entry.expires_at - timezone.now()).total_seconds()) + HOLD_TTL_BUFFER)
    cache.set(f'{HOLD_PREFIX}{hold_token}', json.dumps(entry.to_dict()), ttl)


def get_hold(hold_token: str) -> HoldEntry | None:
    """Lookup hold by token. O(1) Redis get."""
    data = cache.get(f'{HOLD_PREFIX}{hold_token}')
    if data is None:
        return None
    return HoldEntry.from_dict(json.loads(data))


def release_hold(hold_token: str) -> None:
    """Remove hold from registry. O(1) Redis delete."""
    cache.delete(f'{HOLD_PREFIX}{hold_token}')
