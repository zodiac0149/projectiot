import json
import logging
from typing import List, Optional
from datetime import datetime
import requests
from django.conf import settings
from pydantic import ValidationError

from ..schemas import TimeSlot, TaskContext, ReschedulePlan, AllocatedSession
from .heuristic import schedule_tasks_greedy_heuristic

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an algorithmic scheduling engine. You operate deterministically over constraints.
Inputs provided:
1. Available Free Time Slots (Non-overlapping, chronological UTC ranges).
2. Pending Tasks (UUID, Priority 1-5, Estimated Duration, Deadline UTC, Cognitive Load).
3. Disruption Context (User's report of what happened).

Rules:
- Place tasks ONLY within the provided Free Time Slots.
- Never allocate past a task's deadline.
- High cognitive load tasks must preferably be placed in morning slots (08:00 - 12:00 local).
- Split tasks exceeding 90 minutes into multiple sessions with at least 15-minute breaks.
- If a task cannot fit before its deadline, append its UUID to unplaced_task_ids.
- Respond ONLY with valid JSON conforming to the ReschedulePlan schema.
"""

def generate_reschedule_plan(
    free_slots: List[TimeSlot],
    tasks: List[TaskContext],
    disruption_context: str = "Unplanned schedule disruption",
    timeout_seconds: Optional[int] = None
) -> ReschedulePlan:
    """
    Dispatches schedule optimization to the LLM Reasoning Engine with strict JSON schema
    and a hard 12-second latency budget. If the LLM call times out, fails, or violates
    validation rules, gracefully falls back to the deterministic greedy heuristic scheduler.
    """
    if not tasks or not free_slots:
        return ReschedulePlan(
            sessions=[],
            unplaced_task_ids=[t.id for t in tasks]
        )

    timeout = timeout_seconds or getattr(settings, "LLM_TIMEOUT_SECONDS", 12)
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    provider = getattr(settings, "LLM_PROVIDER", "mock")

    # If OpenAI API Key is configured and provider is openai, attempt live inference
    if api_key and provider == "openai":
        try:
            plan = _call_openai_with_timeout(
                api_key=api_key,
                free_slots=free_slots,
                tasks=tasks,
                disruption_context=disruption_context,
                timeout=timeout
            )
            if plan:
                return plan
        except Exception as exc:
            logger.warning(
                "LLM inference encountered error or exceeded %ds budget: %s. Degrading to deterministic heuristic.",
                timeout,
                str(exc)
            )

    # Deterministic fallback (also handles 'mock' mode)
    logger.info("Executing deterministic greedy heuristic scheduler.")
    return schedule_tasks_greedy_heuristic(free_slots=free_slots, tasks=tasks)


def _call_openai_with_timeout(
    api_key: str,
    free_slots: List[TimeSlot],
    tasks: List[TaskContext],
    disruption_context: str,
    timeout: int
) -> Optional[ReschedulePlan]:
    """Invokes OpenAI Chat Completion with strict JSON Schema and timeout."""
    payload = {
        "free_time_slots": [slot.model_dump(mode="json") for slot in free_slots],
        "pending_tasks": [task.model_dump(mode="json") for task in tasks],
        "disruption_context": disruption_context,
    }

    schema = ReschedulePlan.model_json_schema()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "reschedule_plan",
                "strict": True,
                "schema": schema,
            },
        },
        "temperature": 0.1,
    }

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=timeout
    )

    if resp.status_code != 200:
        logger.error("OpenAI API returned status %d: %s", resp.status_code, resp.text)
        return None

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    parsed_json = json.loads(content)
    return ReschedulePlan.model_validate(parsed_json)
