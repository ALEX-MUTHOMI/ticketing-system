"""
Sliding window rate limiter using Redis.

Problem: Prevent checkout abuse — a single user or IP creating hundreds
of holds to starve inventory for real buyers.

Approach: Sliding window counter stored in Redis.
- Key: f"rate:{scope}:{identifier}" (e.g. rate:checkout:ip:1.2.3.4)
- Value: Counter incremented on each request
- TTL: Window duration (e.g. 60 seconds)

Time complexity: O(1) amortised — single Redis INCR + EXPIRE per request.
Space complexity: O(U) where U is unique identifiers in the current window.
"""
from django.core.cache import cache


class RateLimiter:
    def __init__(self, scope: str, limit: int, window_seconds: int):
        self.scope = scope
        self.limit = limit
        self.window_seconds = window_seconds

    def _key(self, identifier: str) -> str:
        return f'rate:{self.scope}:{identifier}'

    def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check if the identifier is within the rate limit.

        Returns:
            (allowed: bool, current_count: int)

        Time complexity: O(1) — single Redis get + incr.
        """
        key = self._key(identifier)
        count = cache.get(key, 0)
        if count >= self.limit:
            return False, count
        # Increment — use add to set TTL on first request, then incr
        if count == 0:
            cache.set(key, 1, self.window_seconds)
            return True, 1
        new_count = cache.incr(key)
        return True, new_count

    def remaining(self, identifier: str) -> int:
        count = cache.get(self._key(identifier), 0)
        return max(0, self.limit - count)


# Pre-configured limiters
checkout_limiter = RateLimiter(scope='checkout', limit=10, window_seconds=60)
login_limiter = RateLimiter(scope='login', limit=5, window_seconds=300)
