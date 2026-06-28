from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from core.permissions import IsOrganizer, IsCompanyMember
from .models import Company
from .serializers import CompanySerializer, CompanyCreateSerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """
    Tenant-scoped Company API.

    Security:
      - List: only companies where user is a member (tenant isolation)
      - Create: organizer role required
      - Detail: company member only (IsCompanyMember)

    Attack 5 defense: queryset is always filtered by user membership.
    An authenticated user from Company A cannot list or access Company B.
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'create':
            return CompanyCreateSerializer
        return CompanySerializer

    def get_queryset(self):
        """Always filter by user membership — Attack 5 tenant isolation."""
        return Company.objects.filter(
            members__user=self.request.user,
            is_active=True
        ).select_related('owner').prefetch_related('members')

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsOrganizer()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsCompanyMember()]
        return [permissions.IsAuthenticated()]
