from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('provider_payment_id', 'provider', 'user', 'company', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('provider', 'status', 'currency')
    search_fields = ('provider_payment_id', 'idempotency_key', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'provider_response')
