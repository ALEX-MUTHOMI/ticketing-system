from rest_framework import viewsets, permissions
from .models import TicketTier
from .serializers import TicketTierSerializer
from core.permissions import IsOrganizer


class TicketTierViewSet(viewsets.ModelViewSet):
    """
    Ticket tier API.

    Public GET — anyone can view available tiers for an event.
    Write operations — organizer only.

    N+1 prevention: queryset uses select_related('event') to avoid
    per-tier event queries in the serializer.
    """
    serializer_class = TicketTierSerializer

    def get_queryset(self):
        qs = TicketTier.objects.select_related('event').filter(is_active=True)
        event_id = self.request.query_params.get('event_id')
        if event_id:
            qs = qs.filter(event_id=event_id)
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsOrganizer()]
        return [permissions.AllowAny()]
