from django.contrib import admin
from .models import CheckoutHold


@admin.register(CheckoutHold)
class CheckoutHoldAdmin(admin.ModelAdmin):
    list_display = ('hold_token', 'user', 'tier', 'quantity', 'status', 'expires_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('hold_token', 'user__email', 'tier__name')
    readonly_fields = ('id', 'hold_token', 'created_at')
