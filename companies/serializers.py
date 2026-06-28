from rest_framework import serializers
from .models import Company, CompanyMember


class CompanySerializer(serializers.ModelSerializer):
    """Explicit field allowlist — no __all__ to prevent mass assignment."""
    class Meta:
        model = Company
        fields = (
            'id', 'name', 'slug', 'plan', 'timezone',
            'logo_url', 'primary_color', 'is_active', 'created_at'
        )
        read_only_fields = ('id', 'slug', 'plan', 'is_active', 'created_at')


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('name', 'timezone', 'logo_url', 'primary_color')

    def create(self, validated_data):
        owner = self.context['request'].user
        return Company.objects.create(owner=owner, **validated_data)


class CompanyMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = CompanyMember
        fields = ('id', 'user_email', 'role', 'joined_at')
        read_only_fields = ('id', 'user_email', 'joined_at')
