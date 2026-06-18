"""
Index existence tests.

Ensures critical DB indexes are not accidentally removed.
CI fails immediately if any index listed below is missing.
"""
import pytest
from django.db import connection


def get_indexes_for_table(table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE tablename = %s",
            [table_name]
        )
        return {row[0] for row in cursor.fetchall()}


@pytest.mark.django_db
class TestCriticalIndexes:
    def test_company_slug_index_exists(self):
        indexes = get_indexes_for_table('companies_company')
        assert 'company_slug_idx' in indexes, 'Missing company_slug_idx — O(N) scan on every company lookup'

    def test_event_company_status_index_exists(self):
        indexes = get_indexes_for_table('events_event')
        assert 'event_company_status_idx' in indexes, 'Missing event_company_status_idx — tenant isolation queries will full scan'

    def test_tier_event_active_index_exists(self):
        indexes = get_indexes_for_table('inventory_tier')
        assert 'tier_event_active_idx' in indexes, 'Missing tier_event_active_idx — tier listing will full scan'
