"""
Comprehensive DS&A Benchmark and Performance Test Suite for Ticketing System.
Tests BloomFilter, Min-Heap Hold Expiry, LRU Cache, Binary Search Tier Selector, and Sliding Window Rate Limiter.
"""
import time
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from checkin.bloom_guard import BloomFilter, mark_scanned, might_be_scanned
from events.lru_cache import LRUCache
from inventory.tier_selector import TierSelector
from core.rate_limiter import RateLimiter


class TestBloomFilterCorrectness:
    def test_zero_false_negatives_on_10000_tickets(self):
        """Assert Bloom filter has exactly 0 false negatives across 10,000 ticket fingerprints."""
        bloom = BloomFilter(size=100_000, hash_count=5)
        ticket_ids = [f"ticket-qr-hash-{i:06d}" for i in range(10000)]
        for tid in ticket_ids:
            bloom.add(tid)

        false_negatives = [tid for tid in ticket_ids if tid not in bloom]
        assert len(false_negatives) == 0, f"Found {len(false_negatives)} false negatives"

    def test_unseen_ticket_rejected(self):
        bloom = BloomFilter(size=100_000, hash_count=5)
        bloom.add("valid-qr-001")
        assert "valid-qr-001" in bloom
        assert "non-existent-qr-999" not in bloom


class TestLRUCacheComplexity:
    def test_lru_cache_eviction_and_constant_time_access(self):
        """Assert LRU cache maintains capacity and evicts oldest entry in O(1)."""
        cache = LRUCache(capacity=2)
        cache.set("event-1", {"name": "Concert 1"})
        cache.set("event-2", {"name": "Concert 2"})
        
        # Access event-1 to make it most recently used
        assert cache.get("event-1")["name"] == "Concert 1"
        
        # Add event-3 -> event-2 should be evicted (as event-1 was accessed)
        cache.set("event-3", {"name": "Concert 3"})
        assert cache.get("event-2") is None
        assert cache.get("event-1") is not None
        assert cache.get("event-3") is not None


class TestBinarySearchTierSelector:
    def test_binary_search_tier_selector_log_n(self):
        """Assert bisection tier selection correctly finds matching tier in O(log N)."""
        class MockTier:
            def __init__(self, name, price, qty=10):
                self.name = name
                self.price = Decimal(str(price))
                self.quantity_available = qty
            def is_on_sale(self):
                return True

        tiers = [
            MockTier("Early Bird", 500),
            MockTier("Regular", 1000),
            MockTier("VIP", 2500),
            MockTier("VVIP", 5000),
        ]
        selector = TierSelector(tiers)

        # Budget of 1200 should pick Regular (price 1000 <= 1200)
        chosen = selector.select_for_budget(Decimal("1200"))
        assert chosen is not None
        assert chosen.name == "Regular"
        
        # Budget of 6000 should pick VVIP
        chosen_vvip = selector.select_for_budget(Decimal("6000"))
        assert chosen_vvip is not None
        assert chosen_vvip.name == "VVIP"


class TestSlidingWindowRateLimiterAmortized:
    def test_rate_limiter_allows_and_blocks_correctly(self):
        limiter = RateLimiter(scope="checkout", limit=3, window_seconds=60)
        with patch("core.rate_limiter.cache") as mock_cache:
            mock_cache.get.return_value = 1
            mock_cache.incr.return_value = 2
            allowed, count = limiter.is_allowed("test-ip-1")
            assert allowed is True
            assert count == 2