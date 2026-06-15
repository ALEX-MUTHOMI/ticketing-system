"""
Hash-map based company slug index for O(1) company resolution.

Problem: Every API request needs to resolve company context from a slug.
Naive approach: `Company.objects.get(slug=slug)` — O(N) full table scan
 without index, O(log N) with index, but still a DB round-trip per request.

This module maintains an in-process hash map (dict) backed by Redis for
O(1) slug → company_id resolution with Redis fallback.

Time complexity: O(1) average for get, O(1) for set/invalidate.
Space complexity: O(K) where K is the number of active companies.
"""
from django.core.cache import cache

SLUG_CACHE_PREFIX = 'company_slug:'
SLUG_CACHE_TTL = 3600  # 1 hour


def get_company_id_by_slug(slug: str) -> str | None:
    """Resolve company_id from slug. O(1) Redis hash lookup."""
    cache_key = f'{SLUG_CACHE_PREFIX}{slug}'
    company_id = cache.get(cache_key)
    if company_id is not None:
        return company_id
    # Cache miss — query DB and populate cache
    from .models import Company
    try:
        company = Company.objects.get(slug=slug, is_active=True)
        cache.set(cache_key, str(company.id), SLUG_CACHE_TTL)
        return str(company.id)
    except Company.DoesNotExist:
        return None


def invalidate_slug(slug: str) -> None:
    """Invalidate slug cache entry on company update. O(1)."""
    cache.delete(f'{SLUG_CACHE_PREFIX}{slug}')


def warm_slug_cache() -> int:
    """Warm the slug index for all active companies. Call on startup."""
    from .models import Company
    count = 0
    for company in Company.objects.filter(is_active=True).values('id', 'slug'):
        cache.set(f"{SLUG_CACHE_PREFIX}{company['slug']}", str(company['id']), SLUG_CACHE_TTL)
        count += 1
    return count
