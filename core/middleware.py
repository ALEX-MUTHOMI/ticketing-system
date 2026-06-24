import uuid
import time
import structlog

logger = structlog.get_logger()


class RequestIDMiddleware:
    """
    Assigns a UUID to every request for audit trail correlation.
    Adds X-Request-ID to responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        response = self.get_response(request)
        response['X-Request-ID'] = request.request_id
        return response


class SecurityHeadersMiddleware:
    """
    Adds security headers to every response.
    Complements Cloudflare Transform Rules in production.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
        return response


class RequestLoggingMiddleware:
    """Structured logging for every request with duration and actor."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        actor = getattr(request.user, 'email', 'anonymous') if hasattr(request, 'user') else 'anonymous'
        logger.info(
            'request',
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration_ms,
            actor=actor,
            request_id=getattr(request, 'request_id', None),
        )
        return response
