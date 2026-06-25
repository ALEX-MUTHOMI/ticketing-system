from rest_framework import permissions


class IsOrganizer(permissions.BasePermission):
    """Allow only users with organizer role. Re-checks DB role — not trusted from JWT."""
    message = 'Organizer role required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'organizer'
        )


class IsEventStaff(permissions.BasePermission):
    """Allow organizers and staff."""
    message = 'Staff or organizer role required.'

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_event_staff()
        )


class IsCompanyMember(permissions.BasePermission):
    """
    Object-level: user must be a member of the object's company.

    Security: This enforces tenant isolation at the permission layer.
    The queryset also filters by company — defense in depth.
    """
    message = 'Not a member of this company.'

    def has_object_permission(self, request, view, obj):
        company = getattr(obj, 'company', None)
        if company is None:
            return False
        from companies.models import CompanyMember
        return CompanyMember.objects.filter(
            company=company, user=request.user
        ).exists()
