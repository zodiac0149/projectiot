from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.scheduler.models import Task, FixedEvent, StudySession
from apps.scheduler.tasks import purge_expired_schedule_events
from apps.scheduler.services.free_time import calculate_free_time_windows
from apps.scheduler.services.heuristic import schedule_tasks_greedy_heuristic
from apps.scheduler.schemas import TaskContext, TimeSlot

User = get_user_model()

class SchedulerCoreTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_engineer", email="eng@university.edu")
        self.now = timezone.now()

    def test_task_soft_delete_and_session_invalidation(self):
        """Verify soft deletion preserves Task while purging phantom future sessions."""
        task = Task.objects.create(
            user=self.user,
            title="Design Distributed Cache",
            priority=5,
            estimated_minutes=120,
            deadline=self.now + timedelta(days=2),
            cognitive_load="HIGH"
        )
        # Create future scheduled session
        future_session = StudySession.objects.create(
            user=self.user,
            task=task,
            start_time=self.now + timedelta(hours=2),
            end_time=self.now + timedelta(hours=4),
            status=StudySession.Status.SCHEDULED
        )

        self.assertEqual(StudySession.objects.filter(task=task).count(), 1)
        task.soft_delete()

        # Task should still exist in DB, marked is_deleted=True
        task.refresh_from_db()
        self.assertTrue(task.is_deleted)
        # Active manager excludes it
        self.assertFalse(Task.active.filter(id=task.id).exists())
        # Future scheduled session was purged
        self.assertEqual(StudySession.objects.filter(task=task).count(), 0)

    def test_purge_expired_schedule_events_celery_task(self):
        """Verify Celery task marks lapsed tasks as EXPIRED and wipes future sessions."""
        # Expired task
        past_task = Task.objects.create(
            user=self.user,
            title="Lapsed Operating Systems Homework",
            priority=3,
            estimated_minutes=60,
            deadline=self.now - timedelta(hours=1),  # In the past
            status=Task.Status.PENDING
        )
        # Active task
        future_task = Task.objects.create(
            user=self.user,
            title="Upcoming Cryptography Quiz Prep",
            priority=4,
            estimated_minutes=90,
            deadline=self.now + timedelta(days=3),
            status=Task.Status.PENDING
        )
        # Future phantom session for the expired task
        StudySession.objects.create(
            user=self.user,
            task=past_task,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=2),
            status=StudySession.Status.SCHEDULED
        )

        purge_expired_schedule_events()

        past_task.refresh_from_db()
        future_task.refresh_from_db()

        self.assertEqual(past_task.status, Task.Status.EXPIRED)
        self.assertTrue(past_task.is_deleted)
        self.assertEqual(future_task.status, Task.Status.PENDING)
        self.assertFalse(future_task.is_deleted)
        self.assertEqual(StudySession.objects.filter(task=past_task).count(), 0)

    def test_free_time_interval_arithmetic(self):
        """Verify mathematical set subtraction of fixed events from study hours."""
        horizon_start = self.now.replace(hour=8, minute=0, second=0, microsecond=0)
        horizon_end = horizon_start + timedelta(days=1)

        # Blocking lecture from 10:00 to 12:00
        lecture_start = horizon_start.replace(hour=10, minute=0)
        lecture_end = horizon_start.replace(hour=12, minute=0)

        slots = calculate_free_time_windows(
            horizon_start=horizon_start,
            horizon_end=horizon_end,
            blocking_events=[(lecture_start, lecture_end)],
            daily_start_hour=8,
            daily_end_hour=14,
            min_slot_minutes=30
        )

        # Expected slots: 08:00 - 10:00 (120 mins) and 12:00 - 14:00 (120 mins)
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0].duration_minutes, 120)
        self.assertEqual(slots[0].start_time, horizon_start)
        self.assertEqual(slots[0].end_time, lecture_start)
        self.assertEqual(slots[1].start_time, lecture_end)

    def test_heuristic_scheduler_rules(self):
        """Verify greedy heuristic splits >90m tasks and respects deadlines."""
        slot_start = self.now.replace(hour=8, minute=0, second=0, microsecond=0)
        free_slots = [
            TimeSlot(
                start_time=slot_start,
                end_time=slot_start + timedelta(hours=4),
                duration_minutes=240
            )
        ]
        tasks = [
            TaskContext(
                id="task-uuid-1",
                title="Deep Learning Lab",
                priority=5,
                estimated_minutes=150,  # > 90 mins, should be split
                deadline=slot_start + timedelta(hours=10),
                cognitive_load="HIGH"
            )
        ]

        plan = schedule_tasks_greedy_heuristic(free_slots, tasks, max_session_minutes=90, break_buffer_minutes=15)
        # Should produce 2 sessions: 90 mins and 60 mins
        self.assertEqual(len(plan.sessions), 2)
        self.assertEqual(len(plan.unplaced_task_ids), 0)
        first_dur = int((plan.sessions[0].end_time - plan.sessions[0].start_time).total_seconds() // 60)
        second_dur = int((plan.sessions[1].end_time - plan.sessions[1].start_time).total_seconds() // 60)
        self.assertEqual(first_dur, 90)
        self.assertEqual(second_dur, 60)
        # Break buffer of 15 mins between sessions
        gap = int((plan.sessions[1].start_time - plan.sessions[0].end_time).total_seconds() // 60)
        self.assertEqual(gap, 15)
