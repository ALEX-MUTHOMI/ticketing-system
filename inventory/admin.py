from django.contrib import admin
from .models import TicketTier


@admin.register(TicketTier)
class TicketTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'currency', 'quantity_total', 'quantity_available', 'is_active')
    list_filter = ('is_active', 'currency', 'event__company')
    search_fields = ('name', 'event__title')
    readonly_fields = ('id', 'created_at', 'quantity_available')
    ordering = ('event', 'sort_order', 'price')
