from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Task, FixedEvent, StudySession
from .schemas import TaskContext
from .serializers import (
    TaskSerializer,
    FixedEventSerializer,
    StudySessionSerializer,
    ReshuffleTriggerSerializer
)
from .services.free_time import calculate_free_time_windows
from .services.llm_engine import generate_reschedule_plan
from .tasks import purge_expired_schedule_events

User = get_user_model()

def get_request_user(request):
    """Helper to return authenticated user or default developer demo user."""
    if request.user.is_authenticated:
        return request.user
    user, _ = User.objects.get_or_create(
        username="engineer_demo",
        defaults={"email": "student@engineering.edu", "first_name": "Alex", "last_name": "Dev"}
    )
    return user


class TaskViewSet(viewsets.ModelViewSet):
    """
    CRUD for Engineering Tasks.
    Enforces soft delete and read-time filtering of deleted entities.
    """
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = get_request_user(self.request)
        include_archived = self.request.query_params.get("all", "false").lower() == "true"
        if include_archived:
            return Task.objects.filter(user=user, is_deleted=False)
        # Default: active only
        return Task.active.filter(user=user)

    def perform_create(self, serializer):
        user = get_request_user(self.request)
        task = serializer.save(user=user)
        # Eliminate Unscheduled Limbo (from new.txt):
        # Automatically slot new tasks on the current day within the 3-day active view
        # allowing the user to immediately view and drag-and-drop elsewhere.
        now = timezone.now()
        duration = task.estimated_minutes or 60
        session_start = now + timedelta(minutes=15)
        if task.deadline and task.deadline < session_start:
            session_start = max(now, task.deadline - timedelta(minutes=duration))
        session_end = session_start + timedelta(minutes=duration)
        StudySession.objects.create(
            user=user,
            task=task,
            start_time=session_start,
            end_time=session_end,
            status=StudySession.Status.SCHEDULED,
            rationale=f"Immediate focus block for {task.title}"
        )

    def perform_update(self, serializer):
        task = serializer.save()
        if task.status == Task.Status.COMPLETED:
            task.sessions.filter(status=StudySession.Status.SCHEDULED).update(status=StudySession.Status.COMPLETED)

    def perform_destroy(self, instance):
        # Spec rule: Soft deletion for tasks, hard deletion for future sessions
        instance.soft_delete()


class FixedEventViewSet(viewsets.ModelViewSet):
    """
    Fixed Calendar Events (Google Calendar Mirror & Hard Commitments).
    Supports sliding date window query optimization: ?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    serializer_class = FixedEventSerializer

    def get_queryset(self):
        user = get_request_user(self.request)
        qs = FixedEvent.objects.filter(user=user)
        start_param = self.request.query_params.get("start")
        end_param = self.request.query_params.get("end")
        if start_param:
            qs = qs.filter(end_time__gte=start_param)
        if end_param:
            qs = qs.filter(start_time__lte=end_param)
        return qs

    def perform_create(self, serializer):
        user = get_request_user(self.request)
        serializer.save(user=user)


def ensure_active_tasks_have_sessions(user):
    """
    Guarantees Zero Unscheduled Limbo (new.txt specification):
    Ensures every active unexpired task has at least one scheduled StudySession.
    If a task has no scheduled session, auto-allocates one before or on its deadline.
    """
    now = timezone.now()
    active_tasks = Task.active.filter(
        user=user,
        status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS],
    )
    for task in active_tasks:
        has_session = StudySession.objects.filter(
            user=user,
            task=task,
            status=StudySession.Status.SCHEDULED,
        ).exists()
        if not has_session:
            duration = task.estimated_minutes or 60
            target_start = task.deadline - timedelta(minutes=duration + 30)
            if target_start < now:
                target_start = now + timedelta(minutes=15)
            target_end = target_start + timedelta(minutes=duration)
            StudySession.objects.create(
                user=user,
                task=task,
                start_time=target_start,
                end_time=target_end,
                status=StudySession.Status.SCHEDULED,
                rationale=f"Auto-allocated focus block for {task.title}"
            )


class StudySessionViewSet(viewsets.ModelViewSet):
    """
    Study Session blocks allocated by the autonomous scheduling engine.
    Supports sliding date window query optimization: ?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    serializer_class = StudySessionSerializer

    def get_queryset(self):
        user = get_request_user(self.request)
        ensure_active_tasks_have_sessions(user)
        now = timezone.now()
        include_completed = self.request.query_params.get("include_completed", "false").lower() == "true"
        qs = StudySession.objects.filter(
            user=user,
            task__is_deleted=False,
            task__deadline__gt=now,
        ).select_related("task")
        if not include_completed:
            qs = qs.filter(status=StudySession.Status.SCHEDULED)
        start_param = self.request.query_params.get("start")
        end_param = self.request.query_params.get("end")
        if start_param:
            qs = qs.filter(end_time__gte=start_param)
        if end_param:
            qs = qs.filter(start_time__lte=end_param)
        return qs

    def perform_create(self, serializer):
        user = get_request_user(self.request)
        serializer.save(user=user)

    def perform_update(self, serializer):
        session = serializer.save()
        if session.status == StudySession.Status.COMPLETED:
            task = session.task
            task.status = Task.Status.COMPLETED
            task.save(update_fields=["status", "updated_at"])


class ReshuffleScheduleView(APIView):
    """
    Emergency Trigger & Autonomous Reshuffle Endpoint:
    POST /api/scheduler/reshuffle/
    Invokes the LLM optimizer (with deterministic greedy fallback) over precomputed free time windows.
    Applies atomic persistence: wipes obsolete scheduled blocks and saves new ones.
    """
    def post(self, request):
        serializer = ReshuffleTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        disruption_context = serializer.validated_data["disruption_context"]
        horizon_days = serializer.validated_data["horizon_days"]

        user = get_request_user(request)
        now = timezone.now()
        horizon_end = now + timedelta(days=horizon_days)

        # 1. Fetch active tasks
        active_tasks = Task.active.filter(
            user=user,
            status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
        )
        if not active_tasks.exists():
            # Seed standard engineering deliverables for demo user if empty
            Task.objects.create(
                user=user,
                title="Implement Raft Consensus State Machine",
                description="Build leader election and log replication module for assignment 3.",
                priority=5,
                estimated_minutes=120,
                deadline=now + timedelta(days=2),
                cognitive_load=Task.CognitiveLoad.HIGH,
                status=Task.Status.PENDING
            )
            Task.objects.create(
                user=user,
                title="FPGA Verilog Pipeline Debugging",
                description="Resolve timing closure violations on the memory controller bus.",
                priority=4,
                estimated_minutes=90,
                deadline=now + timedelta(days=3),
                cognitive_load=Task.CognitiveLoad.HIGH,
                status=Task.Status.PENDING
            )
            Task.objects.create(
                user=user,
                title="Distributed Systems Seminar Review",
                description="Read Google Spanner TrueTime API paper.",
                priority=3,
                estimated_minutes=60,
                deadline=now + timedelta(days=4),
                cognitive_load=Task.CognitiveLoad.MEDIUM,
                status=Task.Status.PENDING
            )
            active_tasks = Task.active.filter(
                user=user,
                status__in=[Task.Status.PENDING, Task.Status.IN_PROGRESS]
            )

        task_contexts = [
            TaskContext(
                id=str(t.id),
                title=t.title,
                priority=t.priority,
                estimated_minutes=t.estimated_minutes,
                deadline=t.deadline,
                cognitive_load=t.cognitive_load
            )
            for t in active_tasks
        ]

        # 2. Fetch fixed events
        fixed_events = FixedEvent.objects.filter(
            user=user,
            end_time__gt=now,
            start_time__lt=horizon_end
        )
        blocking_intervals = [(fe.start_time, fe.end_time) for fe in fixed_events]

        # 3. Compute Free Time Windows
        free_slots = calculate_free_time_windows(
            horizon_start=now,
            horizon_end=horizon_end,
            blocking_events=blocking_intervals
        )

        # 4. Invoke LLM Engine / Heuristic
        plan = generate_reschedule_plan(
            free_slots=free_slots,
            tasks=task_contexts,
            disruption_context=disruption_context
        )

        # 5. Atomic Persistence
        with transaction.atomic():
            # Delete future scheduled sessions for active tasks
            task_ids = [t.id for t in task_contexts]
            StudySession.objects.filter(
                user=user,
                task_id__in=task_ids,
                status=StudySession.Status.SCHEDULED,
                start_time__gte=now
            ).delete()

            # Insert newly scheduled sessions
            created_instances = [
                StudySession(
                    user=user,
                    task_id=session.task_id,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    rationale=session.rationale,
                    status=StudySession.Status.SCHEDULED
                )
                for session in plan.sessions
            ]
            StudySession.objects.bulk_create(created_instances)

        # Fetch freshly populated sessions for the client response
        persisted_sessions = StudySession.objects.filter(
            user=user,
            status=StudySession.Status.SCHEDULED,
            start_time__gte=now
        ).select_related("task")

        return Response(
            {
                "message": "Schedule successfully reallocated.",
                "disruption_context": disruption_context,
                "free_slots_found": len(free_slots),
                "allocated_sessions": StudySessionSerializer(persisted_sessions, many=True).data,
                "unplaced_task_ids": plan.unplaced_task_ids,
            },
            status=status.HTTP_200_OK
        )


class PurgeExpiredView(APIView):
    """
    POST /api/scheduler/purge-expired/
    Manual or webhook-triggered invocation of the 15-minute Celery cleanup cron.
    """
    def post(self, request):
        result_msg = purge_expired_schedule_events()
        return Response({"status": "success", "result": result_msg}, status=status.HTTP_200_OK)
