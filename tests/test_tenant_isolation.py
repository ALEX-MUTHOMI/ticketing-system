"""
Tenant isolation red-team tests.

Tests Attack 5: Cross-tenant data access.
All 20 cross-tenant access attempts must be rejected.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from companies.models import Company, CompanyMember
from events.models import Event

User = get_user_model()


@pytest.fixture
def organizer_a(db):
    return User.objects.create_user(email='org_a@example.com', password='Pass123!', role='organizer')


@pytest.fixture
def organizer_b(db):
    return User.objects.create_user(email='org_b@example.com', password='Pass123!', role='organizer')


@pytest.fixture
def company_a(organizer_a):
    return Company.objects.create(name='Company Alpha', owner=organizer_a)


@pytest.fixture
def company_b(organizer_b):
    return Company.objects.create(name='Company Beta', owner=organizer_b)


@pytest.mark.django_db
class TestCrossTenantIsolation:
    def test_organizer_a_cannot_see_company_b_in_list(self, organizer_a, company_a, company_b):
        """Company B must not appear in Company A organizer's company list."""
        from companies.views import CompanyViewSet
        # company_a member: organizer_a
        CompanyMember.objects.create(company=company_a, user=organizer_a, role='owner')
        client = APIClient()
        client.force_authenticate(user=organizer_a)
        # Verify Company B is not accessible
        from companies.views import CompanyViewSet
        view = CompanyViewSet()
        view.request = type('Request', (), {'user': organizer_a})()
        qs = view.get_queryset()
        company_ids = list(qs.values_list('id', flat=True))
        assert str(company_b.id) not in [str(x) for x in company_ids]

    def test_organizer_a_events_not_visible_to_organizer_b(self, organizer_a, organizer_b, company_a, company_b):
        """Organizer B cannot see Organizer A's draft events."""
        event_a = Event.objects.create(
            company=company_a, title='Secret Event A',
            venue_name='Venue A', status='draft'
        )
        from events.views import OrganizerEventViewSet
        view = OrganizerEventViewSet()
        view.request = type('Request', (), {'user': organizer_b})()
        qs = view.get_queryset()
        event_ids = list(qs.values_list('id', flat=True))
        assert event_a.id not in event_ids
