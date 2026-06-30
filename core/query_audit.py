"""
Query count audit utilities for detecting N+1 problems in tests.

Usage in tests:
    with assert_max_queries(5):
        response = self.client.get('/api/v1/events/')

This catches O(N) query regressions before they reach production.
"""
from contextlib import contextmanager
from django.db import connection, reset_queries
from django.conf import settings


@contextmanager
def assert_max_queries(max_count: int):
    """
    Context manager that asserts the number of DB queries does not exceed max_count.

    Raises:
        AssertionError: If query count exceeds max_count, with a detailed breakdown.
    """
    original_debug = settings.DEBUG
    settings.DEBUG = True  # Required to capture queries
    reset_queries()
    try:
        yield
    finally:
        query_count = len(connection.queries)
        queries = connection.queries
        settings.DEBUG = original_debug
        if query_count > max_count:
            query_summary = '\n'.join(
                f'  [{i+1}] {q["sql"][:120]}...' for i, q in enumerate(queries)
            )
            raise AssertionError(
                f'Expected at most {max_count} queries, got {query_count}.\n'
                f'Queries executed:\n{query_summary}\n'
                f'This is likely an N+1 issue. Add select_related() or prefetch_related().'
            )
