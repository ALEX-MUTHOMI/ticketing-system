from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'actor', 'object_id', 'ip_address', 'created_at')
    list_filter = ('action',)
    search_fields = ('action', 'actor__email', 'object_id')
    readonly_fields = ('id', 'actor', 'action', 'content_type', 'object_id', 'metadata', 'ip_address', 'created_at')

    def has_change_permission(self, request, obj=None):
        return False  # Immutable — no edit

    def has_delete_permission(self, request, obj=None):
        return False  # Immutable — no delete
