import os
from .base import *

DEBUG = True

# Database Configuration with dual mode: Postgres if configured, SQLite fallback for zero-config dev
DB_NAME = os.getenv("POSTGRES_DB")
if DB_NAME:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DB_NAME,
            "USER": os.getenv("POSTGRES_USER", "postgres"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# If Redis is not available locally, Celery tasks execute eagerly (synchronously) in dev mode
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_ALWAYS_EAGER", "True").lower() in ("true", "1")
CELERY_TASK_EAGER_PROPAGATES = True
