from django.contrib import admin
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'attendee', 'tier', 'status', 'issued_at', 'checked_in_at')
    list_filter = ('status', 'tier__event__company')
    search_fields = ('attendee__email', 'qr_fingerprint')
    readonly_fields = ('id', 'qr_fingerprint', 'issued_at', 'checked_in_at')
