import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.development")

celery_app = Celery("study_planner_core")

# Load task-related configuration from Django settings with 'CELERY_' prefix
celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks across registered Django apps
celery_app.autodiscover_tasks()

# Periodic task beat schedule: Layer A Dual-Layer Enforcement
celery_app.conf.beat_schedule = {
    "purge_expired_schedule_events_every_15_mins": {
        "task": "purge_expired_schedule_events",
        "schedule": crontab(minute="*/15"),
    },
}
