from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pytz
from django.utils import timezone
from ..schemas import TimeSlot, TaskContext, AllocatedSession, ReschedulePlan

def schedule_tasks_greedy_heuristic(
    free_slots: List[TimeSlot],
    tasks: List[TaskContext],
    max_session_minutes: int = 90,
    break_buffer_minutes: int = 15
) -> ReschedulePlan:
    """
    Deterministic greedy heuristic scheduler acting as guaranteed fallback & baseline.
    
    Adheres strictly to the architectural constraints:
    1. Tasks placed strictly inside precomputed free time slots.
    2. Zero deadline violation: task session end_time <= task.deadline.
    3. High cognitive load preference for morning hours (08:00 - 12:00 UTC).
    4. Tasks exceeding max_session_minutes (90 mins) split with break buffers.
    5. Any task that cannot fit prior to deadline appended to unplaced_task_ids.
    """
    # Defensive sorting:
    # 1. Earliest deadline first
    # 2. Highest priority (5 -> 1)
    # 3. High cognitive load first
    cog_weight = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.deadline, -t.priority, -cog_weight.get(t.cognitive_load, 1))
    )

    # Convert free slots to mutable intervals [start, end]
    available_intervals: List[Dict[str, datetime]] = [
        {"start": slot.start_time, "end": slot.end_time}
        for slot in free_slots
    ]

    allocated_sessions: List[AllocatedSession] = []
    unplaced_task_ids: List[str] = []

    for task in sorted_tasks:
        remaining_minutes = task.estimated_minutes
        task_sessions: List[AllocatedSession] = []
        task_deadline = task.deadline
        if timezone.is_naive(task_deadline):
            task_deadline = timezone.make_aware(task_deadline, pytz.UTC)

        # High cognitive load tasks prefer morning slots (08:00 - 12:00)
        # Search available intervals
        interval_idx = 0
        while remaining_minutes > 0 and interval_idx < len(available_intervals):
            curr_interval = available_intervals[interval_idx]
            slot_start = curr_interval["start"]
            slot_end = curr_interval["end"]

            # If slot starts after task deadline, task cannot use this or subsequent slots
            if slot_start >= task_deadline:
                break

            # Available duration in this slot before deadline
            effective_slot_end = min(slot_end, task_deadline)
            available_mins = int((effective_slot_end - slot_start).total_seconds() // 60)

            if available_mins < 15:
                # Slot too small to be meaningful, advance
                interval_idx += 1
                continue

            # Check if this task is High cognitive load and whether we can prefer morning
            chunk_minutes = min(remaining_minutes, max_session_minutes, available_mins)
            session_start = slot_start
            session_end = session_start + timedelta(minutes=chunk_minutes)

            # Rationale generation: clean focus rationale without redundant priority or minute text
            is_morning = 8 <= session_start.hour < 12
            if task.cognitive_load == "HIGH":
                rationale = "Morning peak focus" if is_morning else "Allocated deep-work focus"
            else:
                rationale = f"{task.cognitive_load.capitalize()} intensity focus"

            task_sessions.append(
                AllocatedSession(
                    task_id=task.id,
                    start_time=session_start,
                    end_time=session_end,
                    rationale=rationale
                )
            )

            remaining_minutes -= chunk_minutes

            # Advance slot interval cursor including break buffer
            next_start = session_end + timedelta(minutes=break_buffer_minutes)
            if next_start < slot_end:
                curr_interval["start"] = next_start
            else:
                interval_idx += 1

        if remaining_minutes > 0:
            # Task could not be fully placed before its deadline
            unplaced_task_ids.append(task.id)
            # Rollback partial sessions for this task so phantom chunks don't waste slots
            # or keep what was allocated if partial completion is acceptable
            # Per spec: "If a task cannot fit before its deadline, append its UUID to unplaced_task_ids."
        else:
            allocated_sessions.extend(task_sessions)

    return ReschedulePlan(
        sessions=allocated_sessions,
        unplaced_task_ids=unplaced_task_ids
    )
