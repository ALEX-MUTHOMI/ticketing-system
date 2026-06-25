import pytest
from unittest.mock import MagicMock
from core.permissions import IsOrganizer, IsEventStaff, IsCompanyMember


class TestIsOrganizer:
    def test_organizer_allowed(self):
        user = MagicMock(is_authenticated=True, role='organizer')
        request = MagicMock(user=user)
        perm = IsOrganizer()
        assert perm.has_permission(request, None) is True

    def test_attendee_blocked(self):
        """Attack 7: JWT role elevation — attendee cannot access organizer endpoints."""
        user = MagicMock(is_authenticated=True, role='attendee')
        request = MagicMock(user=user)
        perm = IsOrganizer()
        assert perm.has_permission(request, None) is False

    def test_unauthenticated_blocked(self):
        request = MagicMock(user=MagicMock(is_authenticated=False))
        perm = IsOrganizer()
        assert perm.has_permission(request, None) is False


class TestIsEventStaff:
    def test_organizer_is_event_staff(self):
        user = MagicMock(is_authenticated=True)
        user.is_event_staff.return_value = True
        request = MagicMock(user=user)
        perm = IsEventStaff()
        assert perm.has_permission(request, None) is True

    def test_attendee_is_not_event_staff(self):
        """Attack 7: Attendee JWT cannot access staff endpoints."""
        user = MagicMock(is_authenticated=True)
        user.is_event_staff.return_value = False
        request = MagicMock(user=user)
        perm = IsEventStaff()
        assert perm.has_permission(request, None) is False
