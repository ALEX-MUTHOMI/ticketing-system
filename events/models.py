import uuid
from django.db import models


class EventStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    CANCELLED = 'cancelled', 'Cancelled'
    COMPLETED = 'completed', 'Completed'


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    venue_name = models.CharField(max_length=200)
    venue_address = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=EventStatus.choices, default=EventStatus.DRAFT)
    cover_image_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=50, default='Africa/Nairobi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'events_event'
        indexes = [
            models.Index(fields=['company', 'status'], name='event_company_status_idx'),
            models.Index(fields=['status', 'created_at'], name='event_status_created_idx'),
        ]

    def __str__(self):
        return f'{self.title} ({self.company.name})'

    def is_published(self):
        return self.status == EventStatus.PUBLISHED


class EventDate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='dates')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    doors_open = models.DateTimeField(null=True, blank=True)
    label = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'events_date'
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['event', 'start_datetime'], name='eventdate_event_start_idx'),
        ]

    def __str__(self):
        return f'{self.event.title} — {self.start_datetime}'
