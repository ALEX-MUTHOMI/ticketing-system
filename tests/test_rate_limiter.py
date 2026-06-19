import pytest
from unittest.mock import patch, MagicMock
from core.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_first_request_is_allowed(self):
        limiter = RateLimiter(scope='test', limit=5, window_seconds=60)
        with patch('core.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = 0
            allowed, count = limiter.is_allowed('user-1')
            assert allowed is True
            assert count == 1

    def test_request_at_limit_is_blocked(self):
        limiter = RateLimiter(scope='test', limit=5, window_seconds=60)
        with patch('core.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = 5
            allowed, count = limiter.is_allowed('user-1')
            assert allowed is False
            assert count == 5

    def test_remaining_count(self):
        limiter = RateLimiter(scope='test', limit=10, window_seconds=60)
        with patch('core.rate_limiter.cache') as mock_cache:
            mock_cache.get.return_value = 3
            remaining = limiter.remaining('user-1')
            assert remaining == 7

    def test_different_identifiers_are_independent(self):
        limiter = RateLimiter(scope='checkout', limit=2, window_seconds=60)
        with patch('core.rate_limiter.cache') as mock_cache:
            mock_cache.get.side_effect = lambda key, default=0: 2 if 'user-1' in key else 0
            allowed_user1, _ = limiter.is_allowed('user-1')
            allowed_user2, _ = limiter.is_allowed('user-2')
            assert allowed_user1 is False
            assert allowed_user2 is True
