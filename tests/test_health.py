import pytest
from unittest.mock import patch
from django.test import RequestFactory
from core.health import health_check, readiness_check


class TestHealthCheck:
    def test_health_returns_200(self):
        factory = RequestFactory()
        request = factory.get('/health/')
        response = health_check(request)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_readiness_with_db_ok(self):
        factory = RequestFactory()
        request = factory.get('/ready/')
        with patch('core.health.cache') as mock_cache:
            mock_cache.set.return_value = None
            mock_cache.get.return_value = '1'
            response = readiness_check(request)
        import json
        data = json.loads(response.content)
        assert data['checks']['database'] == 'ok'

    def test_readiness_returns_503_on_db_failure(self):
        factory = RequestFactory()
        request = factory.get('/ready/')
        with patch('core.health.connection') as mock_conn, \
             patch('core.health.cache') as mock_cache:
            mock_conn.cursor.side_effect = Exception('DB down')
            mock_cache.set.return_value = None
            mock_cache.get.return_value = '1'
            response = readiness_check(request)
        assert response.status_code == 503
