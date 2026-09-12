import os
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings
import dateutil.parser

from apps.scheduler.models import FixedEvent
from .client import GoogleCalendarClient

logger = logging.getLogger(__name__)
User = get_user_model()

def sync_google_calendar_for_user(user, days_ahead: int = 14) -> int:
    """
    Idempotent synchronization of Google Calendar events into FixedEvent records.
    Guarantee: Running this 10 times produces the exact same state without duplicates.
    """
    now = timezone.now()
    horizon_end = now + timedelta(days=days_ahead)

    token_obj = getattr(user, "google_token", None)
    access_token = token_obj.access_token if token_obj and not token_obj.is_expired() else None

    client = GoogleCalendarClient(access_token=access_token)
    raw_events = client.fetch_primary_calendar_events(time_min=now, time_max=horizon_end)

    synced_count = 0
    with transaction.atomic():
        # When real Google sync runs or in production hosting, automatically purge simulated courses
        enable_mock = getattr(settings, "ENABLE_MOCK_CALENDAR", False) or os.getenv("ENABLE_MOCK_CALENDAR", "").lower() == "true"
        if access_token or not enable_mock:
            FixedEvent.objects.filter(user=user, google_event_id__startswith="gcal_sim_").delete()
        for item in raw_events:
            event_id = item.get("id")
            title = item.get("title", "Untitled")
            start_dt = dateutil.parser.isoparse(item["start_time"])
            end_dt = dateutil.parser.isoparse(item["end_time"])
            is_holiday = item.get("is_holiday", False)

            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt)
            if timezone.is_naive(end_dt):
                end_dt = timezone.make_aware(end_dt)

            # Idempotent upsert via google_event_id
            FixedEvent.objects.update_or_create(
                user=user,
                google_event_id=event_id,
                defaults={
                    "title": title,
                    "start_time": start_dt,
                    "end_time": end_dt,
                    "is_holiday": is_holiday,
                }
            )
            synced_count += 1

    logger.info("Successfully synced %d calendar events for user %s", synced_count, user.username)
    return synced_count
