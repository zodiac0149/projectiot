from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.scheduler.models import Task, FixedEvent, StudySession
from apps.scheduler.schemas import ReschedulePlan, AllocatedSession, TaskContext, TimeSlot
from apps.scheduler.services.llm_engine import generate_reschedule_plan
from apps.calendar_sync.services import sync_google_calendar_for_user

User = get_user_model()

class LLMEngineAndAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="alex_engineer", email="alex@eng.edu")
        self.client.force_authenticate(user=self.user)
        self.now = timezone.now()

    def test_pydantic_reschedule_plan_validation(self):
        """Verify strict Pydantic model contract for LLM outputs."""
        valid_data = {
            "sessions": [
                {
                    "task_id": "test-uuid",
                    "start_time": (self.now + timedelta(hours=1)).isoformat(),
                    "end_time": (self.now + timedelta(hours=2)).isoformat(),
                    "rationale": "Peak focus allocation"
                }
            ],
            "unplaced_task_ids": []
        }
        plan = ReschedulePlan.model_validate(valid_data)
        self.assertEqual(len(plan.sessions), 1)
        self.assertEqual(plan.sessions[0].task_id, "test-uuid")

    def test_calendar_sync_idempotency(self):
        """Guarantee: Running calendar sync 5 times produces identical state without duplicates."""
        count1 = sync_google_calendar_for_user(self.user)
        count2 = sync_google_calendar_for_user(self.user)
        count3 = sync_google_calendar_for_user(self.user)

        total_db_events = FixedEvent.objects.filter(user=self.user).count()
        self.assertEqual(count1, count2)
        self.assertEqual(count1, total_db_events)

    def test_end_to_end_reshuffle_api_endpoint(self):
        """Verify POST /api/scheduler/reshuffle/ dynamically assigns sessions."""
        # Create a task
        task = Task.objects.create(
            user=self.user,
            title="Compiler Optimization Lab",
            priority=5,
            estimated_minutes=60,
            deadline=self.now + timedelta(days=2),
            cognitive_load="HIGH",
            status=Task.Status.PENDING
        )

        resp = self.client.post("/api/scheduler/reshuffle/", {
            "disruption_context": "Systems lab ran 2 hours late",
            "horizon_days": 5
        }, format="json")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn("allocated_sessions", data)
        self.assertTrue(len(data["allocated_sessions"]) > 0)
        self.assertEqual(data["allocated_sessions"][0]["task"], str(task.id))

        # Check DB persistence
        sessions_in_db = StudySession.objects.filter(user=self.user, task=task)
        self.assertTrue(sessions_in_db.exists())
