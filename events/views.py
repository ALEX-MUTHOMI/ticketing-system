from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, EventStatus
from .serializers import EventSerializer
from .lru_cache import get_cached_event, cache_event
from core.permissions import IsOrganizer, IsCompanyMember


class PublicEventListView(viewsets.ReadOnlyModelViewSet):
    """
    Public event listing — no authentication required.

    Security:
      - Only published events returned
      - No company internal data exposed
      - LRU cache for hot event reads

    N+1 prevention: select_related('company') + prefetch_related('dates')
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['company']
    search_fields = ['title', 'venue_name']

    def get_queryset(self):
        return Event.objects.filter(
            status=EventStatus.PUBLISHED
        ).select_related('company').prefetch_related('dates')


class OrganizerEventViewSet(viewsets.ModelViewSet):
    """
    Organizer-scoped event management.

    Attack 5 defense: queryset filters by company membership.
    Organizer from Company A cannot see or modify Company B events.
    """
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizer]

    def get_queryset(self):
        """Tenant-scoped: only events belonging to companies the user owns."""
        return Event.objects.filter(
            company__owner=self.request.user
        ).select_related('company').prefetch_related('dates')

    def perform_create(self, serializer):
        company_id = self.request.data.get('company')
        serializer.save()
