from django.contrib import admin
from .models import WebhookEvent

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('provider', 'event_type', 'provider_event_id', 'processed', 'received_at')
    list_filter = ('provider', 'event_type', 'processed')
    search_fields = ('provider_event_id',)
    readonly_fields = ('id', 'received_at', 'processed_at')
