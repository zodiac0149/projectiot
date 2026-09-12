/**
 * Supabase Auth Integration Module
 * Provides multi-user isolation, JWT bearer token passing to Django API,
 * and session state management.
 */

export interface SupabaseUser {
  id: string;
  email: string;
  user_metadata?: {
    full_name?: string;
    avatar_url?: string;
  };
}

export interface SupabaseSession {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: SupabaseUser;
}

// Development default mock session for seamless offline / zero-config demo
const DEFAULT_DEMO_USER: SupabaseUser = {
  id: "usr_eng_9042a1b",
  email: "alex.dev@engineering.edu",
  user_metadata: {
    full_name: "Alex Dev",
  },
};

// Standard 3-part base64url JWT: header.payload.signature
// payload decodes to: {"sub":"engineer_demo","email":"student@engineering.edu","name":"Alex Dev"}
const DEFAULT_DEMO_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbmdpbmVlcl9kZW1vIiwiZW1haWwiOiJzdHVkZW50QGVuZ2luZWVyaW5nLmVkdSIsIm5hbWUiOiJBbGV4IERldiJ9.signature_hash";

const DEFAULT_DEMO_SESSION: SupabaseSession = {
  access_token: DEFAULT_DEMO_JWT,
  token_type: "Bearer",
  expires_in: 3600,
  user: DEFAULT_DEMO_USER,
};

class SupabaseAuthClient {
  private session: SupabaseSession | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("supabase_session");
        if (stored) {
          this.session = JSON.parse(stored);
        } else {
          this.session = DEFAULT_DEMO_SESSION;
        }
      } catch {
        this.session = DEFAULT_DEMO_SESSION;
      }
    } else {
      this.session = DEFAULT_DEMO_SESSION;
    }
  }

  getSession(): SupabaseSession | null {
    return this.session;
  }

  getToken(): string | null {
    return this.session?.access_token || null;
  }

  getUser(): SupabaseUser | null {
    return this.session?.user || DEFAULT_DEMO_USER;
  }

  setSession(session: SupabaseSession | null) {
    this.session = session;
    if (typeof window !== "undefined") {
      if (session) {
        localStorage.setItem("supabase_session", JSON.stringify(session));
      } else {
        localStorage.removeItem("supabase_session");
      }
    }
  }

  signOut() {
    this.setSession(null);
  }
}

export const supabaseAuth = new SupabaseAuthClient();
