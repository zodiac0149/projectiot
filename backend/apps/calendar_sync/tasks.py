from celery import shared_task
from django.contrib.auth import get_user_model
import logging
from .services import sync_google_calendar_for_user

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(name="sync_all_user_calendars")
def sync_all_user_calendars():
    """
    Celery background sync job to refresh Google Calendar mirrors periodically.
    """
    users = User.objects.all()
    total_synced = 0
    for user in users:
        try:
            count = sync_google_calendar_for_user(user)
            total_synced += count
        except Exception as e:
            logger.error("Failed calendar sync for user %s: %s", user.username, str(e))
    return f"Synced {total_synced} events across {users.count()} users."


@shared_task(name="fetch_google_calendar_events_task")
def fetch_google_calendar_events_task(user_id, days_ahead: int = 30):
    """
    Background Celery task fired immediately after Google OAuth linking
    to fetch the next 30 days of events into the local database.
    """
    try:
        user = User.objects.get(id=user_id)
        count = sync_google_calendar_for_user(user, days_ahead=days_ahead)
        logger.info("30-day Google Calendar sync complete for user %s: %d events.", user.username, count)
        return f"Successfully synced {count} events for user {user.username}."
    except User.DoesNotExist:
        logger.error("User id %s not found for Google Calendar sync.", user_id)
        return f"User {user_id} not found."
    except Exception as e:
        logger.error("Error running 30-day Google Calendar sync for user %s: %s", user_id, str(e))
        return str(e)

