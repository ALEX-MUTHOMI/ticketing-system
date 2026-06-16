"""
LRU Cache for hot event data.

Problem: Popular events receive hundreds of reads per second. Each read
hits PostgreSQL even though the event data rarely changes.

Solution: An LRU (Least Recently Used) cache backed by an OrderedDict.
Implemented manually to demonstrate the data structure, then the
production path uses Django's Redis cache as a distributed LRU.

Time complexity:
  get:  O(1) — hash lookup + move to end
  set:  O(1) — hash insert + move to end
  evict: O(1) — pop from front

Space complexity: O(capacity) — bounded memory footprint.
"""
from collections import OrderedDict
from threading import Lock


class LRUCache:
    """Thread-safe LRU cache using OrderedDict as the underlying structure."""

    def __init__(self, capacity: int = 256):
        self.capacity = capacity
        self._cache: OrderedDict = OrderedDict()
        self._lock = Lock()

    def get(self, key: str):
        """Return cached value or None. O(1) — moves key to end (most recent)."""
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value) -> None:
        """Insert or update. Evicts LRU entry if over capacity. O(1)."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)  # evict LRU (front)

    def invalidate(self, key: str) -> None:
        """Remove a specific key. Called on event update/delete. O(1)."""
        with self._lock:
            self._cache.pop(key, None)

    def __len__(self):
        return len(self._cache)


# Module-level singleton — shared across all requests in the process
_event_cache = LRUCache(capacity=256)


def get_cached_event(event_id: str):
    return _event_cache.get(event_id)


def cache_event(event_id: str, data: dict) -> None:
    _event_cache.set(event_id, data)


def invalidate_event(event_id: str) -> None:
    _event_cache.invalidate(event_id)
