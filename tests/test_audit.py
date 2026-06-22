import pytest
from django.contrib.auth import get_user_model
from audit.models import AuditLog
from audit.services import log_action

User = get_user_model()


@pytest.mark.django_db
class TestAuditLog:
    def test_log_action_creates_entry(self):
        entry = log_action(action='ticket.issued', metadata={'ticket_id': 'abc'})
        assert entry.pk is not None
        assert entry.action == 'ticket.issued'

    def test_audit_log_is_immutable(self):
        entry = log_action(action='test.action')
        with pytest.raises(ValueError, match='immutable'):
            entry.action = 'modified'
            entry.save()

    def test_audit_log_cannot_be_deleted(self):
        entry = log_action(action='test.action')
        with pytest.raises(ValueError, match='cannot be deleted'):
            entry.delete()

    def test_log_with_actor(self):
        user = User.objects.create_user(email='actor@example.com', password='Pass123!')
        entry = log_action(action='payment.succeeded', actor=user, metadata={'amount': '1000'})
        assert entry.actor == user
        assert entry.metadata['amount'] == '1000'
