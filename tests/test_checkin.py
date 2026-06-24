import pytest
from checkin.scan_registry import is_already_checked_in, register_checkin, get_ticket_id_for_qr
from checkin.bloom_guard import BloomFilter, might_be_scanned, mark_scanned


class TestScanRegistry:
    def test_new_qr_not_in_registry(self):
        with __import__('unittest.mock', fromlist=['patch']).patch('checkin.scan_registry.cache') as mock:
            mock.client.get_client.return_value.__enter__ = lambda s: s
            mock.client.get_client.return_value.__exit__ = lambda s, *a: False
            mock.client.get_client.return_value.hexists.return_value = False
            assert is_already_checked_in('unknown-qr') is False


class TestBloomGuard:
    def test_added_item_always_found(self):
        bloom = BloomFilter(size=10_000, hash_count=3)
        fingerprints = [f'fp-{i}' for i in range(100)]
        for fp in fingerprints:
            bloom.add(fp)
        for fp in fingerprints:
            assert fp in bloom, f'{fp} not found — false negative!'

    def test_not_added_item_may_not_be_found(self):
        bloom = BloomFilter(size=100_000, hash_count=5)
        # This item was never added — should return False for a large filter
        assert 'never-added-item-xyz' not in bloom

    def test_bloom_is_O1_for_check(self):
        import time
        bloom = BloomFilter(size=1_000_000, hash_count=7)
        for i in range(10_000):
            bloom.add(f'item-{i}')
        start = time.perf_counter()
        for i in range(1000):
            _ = f'item-{i}' in bloom
        elapsed = time.perf_counter() - start
        avg_us = (elapsed / 1000) * 1_000_000
        assert avg_us < 500, f'Bloom check too slow: {avg_us:.1f}us average (expected <500us)'
