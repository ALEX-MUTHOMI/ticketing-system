from rest_framework import serializers
from .models import TicketTier


class TicketTierSerializer(serializers.ModelSerializer):
    quantity_available = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()

    class Meta:
        model = TicketTier
        fields = (
            'id', 'event', 'name', 'description', 'price', 'currency',
            'quantity_total', 'quantity_available', 'max_per_order',
            'sale_starts_at', 'sale_ends_at', 'is_active', 'is_on_sale', 'sort_order'
        )
        read_only_fields = ('id', 'quantity_available', 'is_on_sale')

    def get_quantity_available(self, obj):
        return obj.quantity_available

    def get_is_on_sale(self, obj):
        return obj.is_on_sale()
