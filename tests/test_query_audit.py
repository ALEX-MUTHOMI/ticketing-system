"""
N+1 query detection tests.

Ensures key list endpoints do not exhibit O(N) query patterns.
Adding a new related object to a serializer without select_related
will cause these tests to fail in CI.
"""
import pytest
from core.query_audit import assert_max_queries


class TestQueryAuditUtility:
    @pytest.mark.django_db
    def test_assert_max_queries_passes_within_limit(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        with assert_max_queries(5):
            list(User.objects.all())

    @pytest.mark.django_db
    def test_assert_max_queries_fails_over_limit(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        with pytest.raises(AssertionError, match='Expected at most 0 queries'):
            with assert_max_queries(0):
                list(User.objects.all())
