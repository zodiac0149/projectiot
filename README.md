# Autonomous, Calendar-Aware Engineering Study Planner (`study-planner-core`)

[![CI Pipeline](https://github.com/organization/study-planner-core/actions/workflows/ci.yml/badge.svg)](https://github.com/organization/study-planner-core/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js: 15+](https://img.shields.io/badge/Next.js-15+-black.svg)](https://nextjs.org/)

An autonomous, calendar-aware engineering study planner that dynamically schedules academic tasks (lectures, labs, competitive prep, capstone milestones) into available time slots by reading Google Calendar for hard commitments. When unexpected disruptions occur (e.g., *"Embedded systems lab ran 2.5 hours late"*), the backend invokes an LLM reasoning engine with strict Pydantic JSON Schema enforcement and a 12-second latency budget, backed by a deterministic greedy heuristic scheduler.

---

## Key System Architecture

```
[ User Input / Calendar Disruption ]
              │
              ▼
[ Django Backend: Ingestion Layer ]
  - Fetch Google Calendar events (FixedEvents)
  - Compute Free Time Windows (Set difference: ActiveHours - FixedEvents)
  - Fetch Active Tasks (Filter: deadline > NOW and status IN ['PENDING', 'IN_PROGRESS'])
              │
              ▼
[ Celery Asynchronous Job / Direct DRF Endpoint ] ──► [ Redis Queue ]
              │
              ▼
[ LLM Dispatcher (services/llm_engine.py) ]
  - Structured Inference (OpenAI / Claude / Bedrock)
  - Fallback to Deterministic Greedy Heuristic (services/heuristic.py)
              │
              ▼
[ Database Persistence (transaction.atomic) ]
  - Atomic bulk update/insert of StudySession records
  - Wipes obsolete scheduled blocks
              │
              ▼
[ Next.js 15+ App Router UI ]
  - Reactive timeline grid, cognitive load indicators, and emergency reshuffle trigger
```

---

## Core Principles & Guarantees

1. **Zero Time Hallucination:** The backend pre-computes valid, non-overlapping free time windows mathematically and supplies them to the scheduler. The optimizer only assigns tasks within confirmed free slots.
2. **Dual-Layer Deadline Purge:** 
   - **Layer A (Celery Beat):** Scheduled cleanup runs every 15 minutes (`purge_expired_schedule_events`), marking expired tasks `EXPIRED` (`is_deleted = True`) and deleting future phantom sessions.
   - **Layer B (Query Isolation):** Custom model manager `Task.active` automatically filters out lapsed or soft-deleted records across all queries.
3. **Deterministic Graceful Degradation:** If the LLM provider times out or errors, the greedy heuristic optimizer allocates sessions without any service interruption.
4. **Idempotency:** Calendar synchronization and cleanup routines produce identical states whether executed once or 10 times in a row.

---

## Local Development Setup

### 1. Backend (Django REST Framework)
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Unix/macOS:
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py test tests/
python manage.py runserver
```

### 2. Frontend (Next.js 15+ App Router)
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to interact with the executive study dashboard.

---

## Docker Orchestration

To run the complete production stack (PostgreSQL 16, Redis 7, Django DRF, Celery Worker, Celery Beat, Next.js):
```bash
docker compose up --build
```
