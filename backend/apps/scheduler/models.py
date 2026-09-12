import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class ActiveTaskManager(models.Manager):
    """
    Query Isolation: Guarantees that inactive, soft-deleted,
    or deadline-lapsed tasks are filtered out at query time.
    """
    def get_queryset(self):
        return super().get_queryset().filter(
            is_deleted=False,
            deadline__gt=timezone.now()
        )

class AllTaskManager(models.Manager):
    """Standard manager exposing all tasks including archived/deleted."""
    pass

class Task(models.Model):
    class CognitiveLoad(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"
        EXPIRED = "EXPIRED", "Expired"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    priority = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 to 5 (5 = Critical)"
    )
    estimated_minutes = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Estimated study duration in minutes (>0)"
    )
    deadline = models.DateTimeField()
    cognitive_load = models.CharField(
        max_length=10,
        choices=CognitiveLoad.choices,
        default=CognitiveLoad.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AllTaskManager()
    active = ActiveTaskManager()

    class Meta:
        ordering = ["deadline", "-priority"]
        indexes = [
            models.Index(
                fields=["user", "deadline"],
                name="idx_tasks_user_deadline",
                condition=models.Q(is_deleted=False)
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(priority__gte=1, priority__lte=5),
                name="chk_task_priority_range"
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_minutes__gt=0),
                name="chk_task_estimated_minutes_positive"
            ),
        ]

    def soft_delete(self):
        """Soft-deletes the task and invalidates scheduled future sessions."""
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])
        # Remove phantom future sessions
        self.sessions.filter(
            status=StudySession.Status.SCHEDULED,
            start_time__gt=timezone.now()
        ).delete()

    def __str__(self) -> str:
        return f"{self.title} (P{self.priority}, {self.status})"


class FixedEvent(models.Model):
    """
    Fixed Calendar Events mirrored from Google Calendar or hard user commitments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fixed_events")
    google_event_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_holiday = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["user", "start_time", "end_time"], name="idx_fixed_events_times"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="chk_fixed_time"
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')})"


class StudySession(models.Model):
    """
    Allocated dynamic study session time block assigned to a task.
    """
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        MISSED = "MISSED", "Missed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="sessions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_sessions")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED
    )
    rationale = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["user", "start_time", "end_time"], name="idx_sessions_user_times"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="chk_session_time"
            )
        ]

    def __str__(self) -> str:
        return f"StudySession: {self.task.title} [{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}]"
