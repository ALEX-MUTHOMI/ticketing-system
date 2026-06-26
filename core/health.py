from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """Basic liveness probe — returns 200 if server is running."""
    return JsonResponse({'status': 'ok'})


def readiness_check(request):
    """
    Readiness probe — checks DB and Redis connectivity.
    Returns 503 if either dependency is unreachable.
    """
    checks = {}
    status_code = 200

    # DB check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {e}'
        status_code = 503

    # Redis check
    try:
        cache.set('_health_check', '1', 5)
        assert cache.get('_health_check') == '1'
        checks['redis'] = 'ok'
    except Exception as e:
        checks['redis'] = f'error: {e}'
        status_code = 503

    return JsonResponse({'status': 'ready' if status_code == 200 else 'not_ready', 'checks': checks}, status=status_code)
