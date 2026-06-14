import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_email(self):
        user = User.objects.create_user(email='test@example.com', password='SecurePass123!')
        assert user.email == 'test@example.com'
        assert user.check_password('SecurePass123!')
        assert user.role == 'attendee'
        assert not user.email_verified

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email='admin@example.com', password='Admin123!')
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.role == 'organizer'

    def test_user_requires_email(self):
        with pytest.raises(ValueError, match='Email is required'):
            User.objects.create_user(email='', password='pass')

    def test_full_name_property(self):
        user = User.objects.create_user(
            email='alex@example.com', password='Pass123!',
            first_name='Alex', last_name='Muthomi'
        )
        assert user.full_name == 'Alex Muthomi'

    def test_is_organizer_role_check(self):
        user = User.objects.create_user(email='org@example.com', password='Pass123!', role='organizer')
        assert user.is_organizer()
        assert user.is_event_staff()

    def test_attendee_is_not_event_staff(self):
        user = User.objects.create_user(email='att@example.com', password='Pass123!')
        assert not user.is_organizer()
        assert not user.is_event_staff()
