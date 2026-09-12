export type CognitiveLoad = "HIGH" | "MEDIUM" | "LOW";

export type TaskStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "EXPIRED" | "ARCHIVED";

export type SessionStatus = "SCHEDULED" | "COMPLETED" | "MISSED";

export interface Task {
  id: string;
  title: string;
  description: string;
  priority: number; // 1 to 5
  estimated_minutes: number;
  deadline: string; // ISO 8601
  cognitive_load: CognitiveLoad;
  status: TaskStatus;
  is_deleted: boolean;
  is_expired?: boolean;
  created_at: string;
  updated_at: string;
}

export interface FixedEvent {
  id: string;
  google_event_id?: string | null;
  title: string;
  start_time: string; // ISO 8601
  end_time: string; // ISO 8601
  is_holiday: boolean;
  created_at: string;
}

export interface StudySession {
  id: string;
  task: string; // task UUID
  task_title?: string;
  task_priority?: number;
  task_cognitive_load?: CognitiveLoad;
  start_time: string; // ISO 8601
  end_time: string; // ISO 8601
  status: SessionStatus;
  rationale: string;
  created_at: string;
}

export interface ReshuffleResponse {
  message: string;
  disruption_context: string;
  free_slots_found: number;
  allocated_sessions: StudySession[];
  unplaced_task_ids: string[];
}

export interface CurrentUser {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  has_google_calendar: boolean;
}
