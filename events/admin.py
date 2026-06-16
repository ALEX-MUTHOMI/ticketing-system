from django.contrib import admin
from .models import Event, EventDate


class EventDateInline(admin.TabularInline):
    model = EventDate
    extra = 1
    fields = ('start_datetime', 'end_datetime', 'doors_open', 'label')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'status', 'venue_name', 'capacity', 'created_at')
    list_filter = ('status', 'company')
    search_fields = ('title', 'venue_name', 'company__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [EventDateInline]


@admin.register(EventDate)
class EventDateAdmin(admin.ModelAdmin):
    list_display = ('event', 'start_datetime', 'end_datetime', 'label')
    list_filter = ('event__company',)
    search_fields = ('event__title',)
