import { Task, FixedEvent, StudySession, ReshuffleResponse, CurrentUser } from "../types";
import { supabaseAuth } from "./supabase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = typeof window !== "undefined" ? supabaseAuth.getToken() : null;

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      const errorBody = await res.text();
      throw new Error(`API error ${res.status}: ${errorBody || res.statusText}`);
    }

    return await res.json();
  } catch (err: any) {
    console.warn(`Fetch to ${endpoint} failed, checking local state:`, err.message);
    throw err;
  }
}

export const api = {
  // Auth & Profile
  async getCurrentUser(): Promise<CurrentUser> {
    return fetchJson<CurrentUser>("/api/auth/me/");
  },

  // Tasks
  async getTasks(includeArchived = false): Promise<Task[]> {
    return fetchJson<Task[]>(`/api/scheduler/tasks/?all=${includeArchived}`);
  },

  async createTask(data: Partial<Task>): Promise<Task> {
    return fetchJson<Task>("/api/scheduler/tasks/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateTask(id: string, data: Partial<Task>): Promise<Task> {
    return fetchJson<Task>(`/api/scheduler/tasks/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteTask(id: string): Promise<void> {
    await fetchJson<void>(`/api/scheduler/tasks/${id}/`, {
      method: "DELETE",
    });
  },

  // Fixed Calendar Events
  async getFixedEvents(start?: string, end?: string): Promise<FixedEvent[]> {
    const params = new URLSearchParams();
    if (start) params.append("start", start);
    if (end) params.append("end", end);
    const query = params.toString() ? `?${params.toString()}` : "";
    return fetchJson<FixedEvent[]>(`/api/scheduler/fixed-events/${query}`);
  },

  async createFixedEvent(data: Partial<FixedEvent>): Promise<FixedEvent> {
    return fetchJson<FixedEvent>("/api/scheduler/fixed-events/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Study Sessions
  async getStudySessions(start?: string, end?: string): Promise<StudySession[]> {
    const params = new URLSearchParams();
    if (start) params.append("start", start);
    if (end) params.append("end", end);
    const query = params.toString() ? `?${params.toString()}` : "";
    return fetchJson<StudySession[]>(`/api/scheduler/sessions/${query}`);
  },

  async updateSessionStatus(id: string, status: "SCHEDULED" | "COMPLETED" | "MISSED"): Promise<StudySession> {
    return fetchJson<StudySession>(`/api/scheduler/sessions/${id}/`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
  },

  async updateSessionTime(id: string, startTimeIso: string, endTimeIso: string): Promise<StudySession> {
    return fetchJson<StudySession>(`/api/scheduler/sessions/${id}/`, {
      method: "PATCH",
      body: JSON.stringify({
        start_time: startTimeIso,
        end_time: endTimeIso,
      }),
    });
  },

  // Reshuffle Engine
  async triggerReshuffle(disruptionContext: string, horizonDays = 7): Promise<ReshuffleResponse> {
    return fetchJson<ReshuffleResponse>("/api/scheduler/reshuffle/", {
      method: "POST",
      body: JSON.stringify({
        disruption_context: disruptionContext,
        horizon_days: horizonDays,
      }),
    });
  },

  // Google Calendar Sync & OAuth
  async syncGoogleCalendar(): Promise<{ status: string; message: string; synced_count: number }> {
    return fetchJson("/api/calendar/sync/", {
      method: "POST",
    });
  },

  async getGoogleOAuthStatus(): Promise<{ is_connected: boolean; scopes?: string; expires_at?: string; user_email?: string }> {
    return fetchJson("/api/calendar/oauth/status/");
  },

  async getGoogleOAuthLoginUrl(): Promise<{ status: string; auth_url: string; callback_uri: string; client_configured: boolean }> {
    return fetchJson("/api/calendar/oauth/login/");
  },

  async disconnectGoogleOAuth(): Promise<{ status: string; message: string }> {
    return fetchJson("/api/calendar/oauth/disconnect/", {
      method: "POST",
    });
  },

  // Deadline Expiration Purge
  async triggerPurgeExpired(): Promise<{ status: string; result: string }> {
    return fetchJson("/api/scheduler/purge-expired/", {
      method: "POST",
    });
  },
};

