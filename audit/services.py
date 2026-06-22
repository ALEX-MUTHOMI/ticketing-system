from .models import AuditLog
from django.contrib.contenttypes.models import ContentType


def log_action(action: str, actor=None, entity=None, metadata: dict = None, ip_address: str = None):
    """
    Append an immutable audit log entry.
    This is a write-only operation — no updates or deletes.
    """
    entry = AuditLog(
        actor=actor,
        action=action,
        metadata=metadata or {},
        ip_address=ip_address,
    )
    if entity is not None:
        ct = ContentType.objects.get_for_model(entity)
        entry.content_type = ct
        entry.object_id = entity.pk
    entry.save()
    return entry
