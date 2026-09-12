from datetime import datetime, timedelta, time
from typing import List, Tuple, Sequence
import pytz
from django.utils import timezone
from ..schemas import TimeSlot

def calculate_free_time_windows(
    horizon_start: datetime,
    horizon_end: datetime,
    blocking_events: Sequence[Tuple[datetime, datetime]],
    daily_start_hour: int = 8,
    daily_end_hour: int = 22,
    min_slot_minutes: int = 30
) -> List[TimeSlot]:
    """
    Computes deterministic, non-overlapping free time windows between horizon_start
    and horizon_end, strictly subtracting fixed events and respecting daily study hours.
    
    Guarantees:
    - Zero time hallucination: slots are mathematical set differences.
    - Chronologically ordered UTC time windows.
    - Filters out sliver slots (< min_slot_minutes).
    """
    if horizon_start >= horizon_end:
        return []

    # Ensure UTC timezone awareness
    if timezone.is_naive(horizon_start):
        horizon_start = timezone.make_aware(horizon_start, pytz.UTC)
    if timezone.is_naive(horizon_end):
        horizon_end = timezone.make_aware(horizon_end, pytz.UTC)

    # 1. Normalize and merge blocking events
    clean_blocks: List[Tuple[datetime, datetime]] = []
    for b_start, b_end in blocking_events:
        if timezone.is_naive(b_start):
            b_start = timezone.make_aware(b_start, pytz.UTC)
        if timezone.is_naive(b_end):
            b_end = timezone.make_aware(b_end, pytz.UTC)
        
        # Clamp to horizon
        c_start = max(b_start, horizon_start)
        c_end = min(b_end, horizon_end)
        if c_end > c_start:
            clean_blocks.append((c_start, c_end))

    # Sort and merge overlapping blocks
    clean_blocks.sort(key=lambda x: x[0])
    merged_blocks: List[Tuple[datetime, datetime]] = []
    for block in clean_blocks:
        if not merged_blocks:
            merged_blocks.append(block)
        else:
            prev_start, prev_end = merged_blocks[-1]
            if block[0] <= prev_end:
                merged_blocks[-1] = (prev_start, max(prev_end, block[1]))
            else:
                merged_blocks.append(block)

    # 2. Iterate day by day within [horizon_start, horizon_end]
    current_date = horizon_start.date()
    end_date = horizon_end.date()
    free_slots: List[TimeSlot] = []

    while current_date <= end_date:
        day_start = timezone.make_aware(
            datetime.combine(current_date, time(hour=daily_start_hour, minute=0)),
            pytz.UTC
        )
        day_end = timezone.make_aware(
            datetime.combine(current_date, time(hour=daily_end_hour, minute=0)),
            pytz.UTC
        )

        # Restrict day window to horizon bounds
        window_start = max(day_start, horizon_start)
        window_end = min(day_end, horizon_end)

        if window_end > window_start:
            # Subtract all blocks intersecting [window_start, window_end]
            cursor = window_start
            for b_start, b_end in merged_blocks:
                if b_end <= cursor:
                    continue
                if b_start >= window_end:
                    break

                if b_start > cursor:
                    slot_dur = int((min(b_start, window_end) - cursor).total_seconds() // 60)
                    if slot_dur >= min_slot_minutes:
                        free_slots.append(
                            TimeSlot(
                                start_time=cursor,
                                end_time=min(b_start, window_end),
                                duration_minutes=slot_dur
                            )
                        )
                cursor = max(cursor, b_end)

            if cursor < window_end:
                slot_dur = int((window_end - cursor).total_seconds() // 60)
                if slot_dur >= min_slot_minutes:
                    free_slots.append(
                        TimeSlot(
                            start_time=cursor,
                            end_time=window_end,
                            duration_minutes=slot_dur
                        )
                    )

        current_date += timedelta(days=1)

    return free_slots
