import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class GoogleCalendarClient:
    """
    Google Calendar API v3 client wrapper.
    Supports live OAuth token integration and defensive simulation when offline.
    """
    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    def fetch_primary_calendar_events(
        self,
        time_min: datetime,
        time_max: datetime
    ) -> List[Dict[str, Any]]:
        """
        Fetches calendar events between time_min and time_max.
        Returns list of standardized event dicts:
        [{ 'id': ..., 'summary': ..., 'start': ..., 'end': ..., 'is_holiday': ... }]
        """
        if self.access_token:
            try:
                import requests
                headers = {"Authorization": f"Bearer {self.access_token}"}
                params = {
                    "timeMin": time_min.isoformat(),
                    "timeMax": time_max.isoformat(),
                    "singleEvents": "true",
                    "orderBy": "startTime",
                }
                resp = requests.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers=headers,
                    params=params,
                    timeout=10
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    return [
                        {
                            "id": item.get("id"),
                            "title": item.get("summary", "Untitled Event"),
                            "start_time": item["start"].get("dateTime", item["start"].get("date")),
                            "end_time": item["end"].get("dateTime", item["end"].get("date")),
                            "is_holiday": "holiday" in item.get("summary", "").lower(),
                        }
                        for item in items
                        if "start" in item and "end" in item
                    ]
            except Exception as e:
                logger.error("Error connecting to Google Calendar API: %s", str(e))

        # Built-in sample academic schedule: only generated in local development mode
        # when ENABLE_MOCK_CALENDAR=true. In production / hosting, this is strictly disabled.
        enable_mock = getattr(settings, "ENABLE_MOCK_CALENDAR", False) or os.getenv("ENABLE_MOCK_CALENDAR", "").lower() == "true"
        if getattr(settings, "DEBUG", False) and enable_mock:
            return self._generate_sample_academic_calendar(time_min)

        return []

    def _generate_sample_academic_calendar(self, base_time: datetime) -> List[Dict[str, Any]]:
        """Generates representative university calendar events for instant testing."""
        events = []
        base_day = base_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # Day 1: Systems Architecture Lecture
        events.append({
            "id": "gcal_sim_lecture_1",
            "title": "CS401: Distributed Systems Lecture",
            "start_time": (base_day + timedelta(days=0, hours=10)).isoformat(),
            "end_time": (base_day + timedelta(days=0, hours=11, minutes=30)).isoformat(),
            "is_holiday": False,
        })
        # Day 1: Embedded Systems Lab
        events.append({
            "id": "gcal_sim_lab_1",
            "title": "EE302: Embedded Systems Hardware Lab",
            "start_time": (base_day + timedelta(days=0, hours=14)).isoformat(),
            "end_time": (base_day + timedelta(days=0, hours=16, minutes=30)).isoformat(),
            "is_holiday": False,
        })
        # Day 2: Algorithms Colloquium
        events.append({
            "id": "gcal_sim_lecture_2",
            "title": "CS450: Algorithms & Complexity Seminar",
            "start_time": (base_day + timedelta(days=1, hours=11)).isoformat(),
            "end_time": (base_day + timedelta(days=1, hours=12, minutes=30)).isoformat(),
            "is_holiday": False,
        })
        # Day 3: Department Project Review
        events.append({
            "id": "gcal_sim_review_3",
            "title": "Capstone Engineering Milestone Review",
            "start_time": (base_day + timedelta(days=2, hours=15)).isoformat(),
            "end_time": (base_day + timedelta(days=2, hours=17)).isoformat(),
            "is_holiday": False,
        })
        return events
