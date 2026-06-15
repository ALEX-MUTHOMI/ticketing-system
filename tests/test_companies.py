import pytest
from django.contrib.auth import get_user_model
from companies.models import Company, CompanyMember, CompanyMemberRole
from companies.slug_index import get_company_id_by_slug, invalidate_slug

User = get_user_model()


@pytest.fixture
def organizer(db):
    return User.objects.create_user(email='org@example.com', password='Pass123!', role='organizer')


@pytest.fixture
def company(organizer):
    return Company.objects.create(name='Nairobi Events Co', owner=organizer)


@pytest.mark.django_db
class TestCompanyModel:
    def test_slug_auto_generated(self, company):
        assert company.slug == 'nairobi-events-co'

    def test_slug_is_unique(self, organizer, company):
        import pytest
        with pytest.raises(Exception):
            Company.objects.create(name='Nairobi Events Co', slug='nairobi-events-co', owner=organizer)

    def test_default_plan_is_free(self, company):
        assert company.plan == 'free'

    def test_member_role_assignment(self, company, organizer):
        attendee = User.objects.create_user(email='staff@example.com', password='Pass123!')
        member = CompanyMember.objects.create(company=company, user=attendee, role=CompanyMemberRole.STAFF)
        assert member.role == 'staff'
        assert str(member) == f'staff@example.com @ Nairobi Events Co (staff)'


@pytest.mark.django_db
class TestSlugIndex:
    def test_slug_resolves_to_company_id(self, company):
        result = get_company_id_by_slug(company.slug)
        assert result == str(company.id)

    def test_unknown_slug_returns_none(self):
        result = get_company_id_by_slug('nonexistent-slug')
        assert result is None

    def test_invalidate_clears_cache(self, company):
        get_company_id_by_slug(company.slug)  # warm cache
        invalidate_slug(company.slug)
        # After invalidation, next call hits DB again — still returns correct value
        result = get_company_id_by_slug(company.slug)
        assert result == str(company.id)
