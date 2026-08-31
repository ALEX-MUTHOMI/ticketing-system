import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
application = get_wsgi_application()

# Pre-warm drf-spectacular's lazy class cache once per worker process (single
# threaded, at import time) so concurrent threaded requests to /api/schema/ do
# not race while populating drf_spectacular.plumbing._load_class's global cache
# (which otherwise leaks an ImportError for optional integrations as a 500).
# Best-effort: never let schema warm-up prevent the app from starting.
try:
    from drf_spectacular.generators import SchemaGenerator

    SchemaGenerator().get_schema(request=None, public=True)
except Exception:
    pass
