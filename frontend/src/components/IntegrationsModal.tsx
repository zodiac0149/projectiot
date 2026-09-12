"use client";

import React, { useState, useEffect } from "react";
import { 
  X, 
  Calendar as CalendarIcon, 
  ShieldCheck, 
  CheckCircle2, 
  RefreshCw, 
  ExternalLink,
  Layers,
  Key,
  UserCheck,
  Unlink
} from "lucide-react";
import { api } from "../lib/api";

interface IntegrationsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSyncCalendar: () => Promise<void>;
  isSyncing: boolean;
  hasGoogleConnected?: boolean;
  userEmail?: string;
  userId?: string;
}

export const IntegrationsModal: React.FC<IntegrationsModalProps> = ({
  isOpen,
  onClose,
  onSyncCalendar,
  isSyncing,
  hasGoogleConnected = true,
  userEmail = "alex.dev@engineering.edu",
  userId = "usr_eng_9042a1b",
}) => {
  const [isConnected, setIsConnected] = useState(hasGoogleConnected);
  const [isLinking, setIsLinking] = useState(false);

  useEffect(() => {
    if (isOpen) {
      api.getGoogleOAuthStatus()
        .then((res) => {
          if (res && typeof res.is_connected === "boolean") {
            setIsConnected(res.is_connected);
          }
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleLinkGoogle = async () => {
    setIsLinking(true);
    try {
      const res = await api.getGoogleOAuthLoginUrl();
      if (res.client_configured) {
        window.location.href = res.auth_url;
      } else {
        // Local developer mode: use callback endpoint to simulate token exchange & 30-day sync
        window.location.href = `${res.callback_uri}?code=local_demo_auth_code`;
      }
    } catch {
      // Fallback
      await onSyncCalendar();
      setIsConnected(true);
    } finally {
      setIsLinking(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await api.disconnectGoogleOAuth();
      setIsConnected(false);
    } catch {
      setIsConnected(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-panel rounded-2xl w-full max-w-xl border border-slate-700 shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              Settings & Third-Party Integrations
            </h3>
            <p className="text-xs text-slate-400">
              Manage your Google Calendar OAuth connection and authentication state
            </p>
          </div>
        </div>

        <div className="space-y-4 text-xs">
          {/* Google Calendar Integration Card */}
          <div className="rounded-xl p-4 bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-white flex items-center justify-center shadow-sm p-1.5 shrink-0">
                  {/* Google SVG Icon */}
                  <svg className="w-full h-full" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                </div>
                <div>
                  <h4 className="font-bold text-sm text-white">Google Calendar</h4>
                  <p className="text-slate-400 mt-0.5">
                    Two-way synchronization for university lectures, labs, and personal commitments
                  </p>
                </div>
              </div>

              {isConnected && (
                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold shrink-0">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Linked</span>
                </span>
              )}
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
              <span className="text-slate-400 text-[11px]">
                {isConnected ? "Synced automatically via Celery background tasks" : "Connect your Google account"}
              </span>

              <div className="flex items-center space-x-2">
                {isConnected && (
                  <>
                    <button
                      onClick={handleDisconnect}
                      className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 transition"
                      title="Unlink Google Calendar"
                    >
                      <Unlink className="w-3.5 h-3.5 text-rose-400" />
                      <span>Unlink</span>
                    </button>

                    <button
                      onClick={onSyncCalendar}
                      disabled={isSyncing}
                      className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition disabled:opacity-50"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isSyncing ? "animate-spin" : ""}`} />
                      <span>{isSyncing ? "Syncing..." : "Sync Now"}</span>
                    </button>
                  </>
                )}

                <button
                  onClick={handleLinkGoogle}
                  disabled={isLinking}
                  className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-bold text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-50"
                >
                  <CalendarIcon className="w-3.5 h-3.5 text-white" />
                  <span>{isLinking ? "Redirecting..." : isConnected ? "Re-link Calendar" : "Link Google Calendar"}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Authentication & Supabase Details Card */}
          <div className="rounded-xl p-4 bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0">
                <UserCheck className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-white">Supabase / User Auth</h4>
                <p className="text-slate-400">Row-Level Security (RLS) and multi-user isolation</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800/80 font-mono text-[11px]">
              <div>
                <span className="text-slate-500 block">User Account:</span>
                <span className="text-slate-200 font-semibold truncate block">{userEmail}</span>
              </div>
              <div>
                <span className="text-slate-500 block">User ID:</span>
                <span className="text-slate-400 truncate block">{userId}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 mt-4 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
