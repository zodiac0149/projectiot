from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from .models import Task, StudySession, FixedEvent
from .schemas import TaskContext
from .services.free_time import calculate_free_time_windows
from .services.llm_engine import generate_reschedule_plan

logger = logging.getLogger(__name__)

@shared_task(name="purge_expired_schedule_events")
def purge_expired_schedule_events():
    """
    Layer A: Dual-Layer Automated Scheduled Cleanup (Celery Beat Cron).
    Runs every 15 minutes to evaluate expired tasks and update states transactionally.
    Zero UI clutter, minimize LLM context window, maintain database index efficiency.
    """
    now = timezone.now()
    
    with transaction.atomic():
        expired_tasks = Task.objects.filter(
            deadline__lt=now,
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
            is_deleted=False
        )
        
        expired_task_ids = list(expired_tasks.values_list("id", flat=True))
        
        if expired_task_ids:
            # 1. Soft-delete and mark EXPIRED on Tasks
            expired_tasks.update(status=Task.Status.EXPIRED, is_deleted=True, updated_at=now)
            
        # 2. Invalidate all completed, missed, or expired task sessions
        del_count, _ = StudySession.objects.filter(
            task__is_deleted=True
        ).delete()
        del_count2, _ = StudySession.objects.filter(
            status__in=[StudySession.Status.COMPLETED, StudySession.Status.MISSED]
        ).delete()
        del_count3, _ = StudySession.objects.filter(
            task__deadline__lt=now
        ).delete()
            
    summary = f"Purged completed/expired sessions and {len(expired_task_ids)} expired tasks."
    logger.info(summary)
    return summary


@shared_task(name="async_recalculate_user_schedule")
def async_recalculate_user_schedule(user_id: str, disruption_context: str = "Automated Reschedule", horizon_days: int = 7):
    """
    Asynchronous task executing end-to-end schedule recalculation:
    1. Fetch active tasks & fixed events
    2. Calculate free time windows
    3. Run LLM optimization (with deterministic fallback)
    4. Atomically persist updated StudySession records
    """
    now = timezone.now()
    horizon_end = now + timedelta(days=horizon_days)

    # Fetch active tasks
    tasks_qs = Task.active.filter(user_id=user_id, status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS])
    if not tasks_qs.exists():
        return {"status": "noop", "message": "No active tasks found for user"}

    task_contexts = [
        TaskContext(
            id=str(t.id),
            title=t.title,
            priority=t.priority,
            estimated_minutes=t.estimated_minutes,
            deadline=t.deadline,
            cognitive_load=t.cognitive_load
        )
        for t in tasks_qs
    ]

    # Fetch fixed calendar events
    fixed_qs = FixedEvent.objects.filter(
        user_id=user_id,
        end_time__gt=now,
        start_time__lt=horizon_end
    )
    blocking_intervals = [(fe.start_time, fe.end_time) for fe in fixed_qs]

    # Free time windows
    free_slots = calculate_free_time_windows(
        horizon_start=now,
        horizon_end=horizon_end,
        blocking_events=blocking_intervals
    )

    # LLM inference / heuristic
    plan = generate_reschedule_plan(
        free_slots=free_slots,
        tasks=task_contexts,
        disruption_context=disruption_context
    )

    # Atomic persistence
    with transaction.atomic():
        # Clear out future scheduled sessions for active tasks to avoid duplication
        active_task_ids = [t.id for t in task_contexts]
        StudySession.objects.filter(
            user_id=user_id,
            task_id__in=active_task_ids,
            status=StudySession.Status.SCHEDULED,
            start_time__gte=now
        ).delete()

        # Bulk insert new study sessions
        new_sessions = [
            StudySession(
                user_id=user_id,
                task_id=session.task_id,
                start_time=session.start_time,
                end_time=session.end_time,
                rationale=session.rationale,
                status=StudySession.Status.SCHEDULED
            )
            for session in plan.sessions
        ]
        StudySession.objects.bulk_create(new_sessions)

    return {
        "status": "success",
        "allocated_sessions": len(plan.sessions),
        "unplaced_tasks": plan.unplaced_task_ids
    }
