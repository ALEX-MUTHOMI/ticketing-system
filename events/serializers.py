from rest_framework import serializers
from .models import Event, EventDate


class EventDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDate
        fields = ('id', 'start_datetime', 'end_datetime', 'doors_open', 'label')


class EventSerializer(serializers.ModelSerializer):
    dates = EventDateSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = (
            'id', 'company', 'title', 'description', 'venue_name',
            'venue_address', 'capacity', 'status', 'cover_image_url',
            'timezone', 'dates', 'created_at'
        )
        read_only_fields = ('id', 'company', 'created_at')
