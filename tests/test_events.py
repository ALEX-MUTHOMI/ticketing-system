import pytest
from django.contrib.auth import get_user_model
from companies.models import Company
from events.models import Event, EventStatus
from events.lru_cache import LRUCache, get_cached_event, cache_event, invalidate_event

User = get_user_model()


@pytest.fixture
def organizer(db):
    return User.objects.create_user(email='org@example.com', password='Pass123!', role='organizer')


@pytest.fixture
def company(organizer):
    return Company.objects.create(name='Test Events Ltd', owner=organizer)


@pytest.fixture
def event(company):
    return Event.objects.create(
        company=company, title='Nairobi Jazz Fest',
        venue_name='KICC', capacity=500
    )


@pytest.mark.django_db
class TestEventModel:
    def test_event_default_status_is_draft(self, event):
        assert event.status == EventStatus.DRAFT
        assert not event.is_published()

    def test_event_publish_state_transition(self, event):
        event.status = EventStatus.PUBLISHED
        event.save()
        assert event.is_published()

    def test_event_belongs_to_company(self, event, company):
        assert event.company == company


class TestLRUCache:
    def test_get_returns_none_on_miss(self):
        cache = LRUCache(capacity=3)
        assert cache.get('missing') is None

    def test_set_and_get(self):
        cache = LRUCache(capacity=3)
        cache.set('k1', {'id': '1', 'title': 'Event A'})
        result = cache.get('k1')
        assert result['title'] == 'Event A'

    def test_evicts_lru_when_over_capacity(self):
        cache = LRUCache(capacity=2)
        cache.set('k1', 'val1')
        cache.set('k2', 'val2')
        cache.get('k1')  # access k1 — makes k2 the LRU
        cache.set('k3', 'val3')  # should evict k2
        assert cache.get('k2') is None
        assert cache.get('k1') == 'val1'
        assert cache.get('k3') == 'val3'

    def test_invalidate_removes_key(self):
        cache = LRUCache(capacity=3)
        cache.set('k1', 'val1')
        cache.invalidate('k1')
        assert cache.get('k1') is None

    def test_cache_is_bounded(self):
        cache = LRUCache(capacity=5)
        for i in range(10):
            cache.set(f'key{i}', f'val{i}')
        assert len(cache) == 5
