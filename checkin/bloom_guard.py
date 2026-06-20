"""
Bloom filter for QR duplicate scan detection.

Problem: At high-volume events (10,000+ attendees), the scan registry hash
map holds all checked-in fingerprints. We want a probabilistic first-pass
check before even hitting Redis HEXISTS.

Bloom Filter properties:
  - Space-efficient: uses a bit array, not full fingerprints
  - O(1) lookup and insert
  - Zero false-negatives: if we say NOT in set, it definitely is NOT
  - Small false-positive rate: ~0.1% at 10k entries with our parameters
    (false positive = says checked in when it isn't — caught by hash map fallback)

Implementation: Pure Python bit array with 3 hash functions.
For production, use Redis BF.ADD / BF.EXISTS via RedisBloom module.
"""
import hashlib
from array import array


class BloomFilter:
    def __init__(self, size: int = 100_000, hash_count: int = 3):
        """
        Args:
            size: Bit array size. 100k bits = ~12KB.
            hash_count: Number of hash functions.

        For 10,000 items and 0.1% FPR:
          size ~ 143,775 bits, hash_count ~ 10
        """
        self.size = size
        self.hash_count = hash_count
        self._bits = array('b', [0] * size)

    def _hashes(self, item: str):
        """Generate hash_count independent hash positions. O(1)."""
        item_bytes = item.encode()
        for i in range(self.hash_count):
            digest = hashlib.sha256(f'{i}:{item}'.encode()).hexdigest()
            yield int(digest[:8], 16) % self.size

    def add(self, item: str) -> None:
        """Insert item. O(hash_count) = O(1) since hash_count is constant."""
        for pos in self._hashes(item):
            self._bits[pos] = 1

    def __contains__(self, item: str) -> bool:
        """
        Check if item might be in the set. O(1).

        Returns:
            False: Definitely NOT in set. Zero false-negatives.
            True:  Probably in set (may be false positive, ~0.1% rate).
        """
        return all(self._bits[pos] for pos in self._hashes(item))


# Process-level singleton for the running event day
_scan_bloom = BloomFilter(size=200_000, hash_count=5)


def might_be_scanned(qr_fingerprint: str) -> bool:
    """Fast probabilistic check. If False, definitely not scanned."""
    return qr_fingerprint in _scan_bloom


def mark_scanned(qr_fingerprint: str) -> None:
    """Add fingerprint to bloom filter after confirmed check-in."""
    _scan_bloom.add(qr_fingerprint)
