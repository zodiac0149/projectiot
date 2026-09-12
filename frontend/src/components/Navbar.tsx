"use client";

import React, { useState, useRef, useEffect } from "react";
import { 
  AlertTriangle, 
  Clock, 
  Layers,
  RefreshCw,
  User,
  Settings,
  ChevronDown,
  Calendar,
  CheckCircle2
} from "lucide-react";

interface NavbarProps {
  onTriggerReshuffle: () => void;
  onOpenSettings: () => void;
  onSyncCalendar: () => Promise<void>;
  isSyncing: boolean;
  activeTasksCount: number;
  userName?: string;
  userEmail?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onTriggerReshuffle,
  onOpenSettings,
  onSyncCalendar,
  isSyncing,
  activeTasksCount,
  userName = "Alex Dev",
  userEmail = "alex.dev@engineering.edu",
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-slate-800/80 px-6 py-3 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-tight text-white">
              StudyPlanner<span className="text-cyan-400">Core</span>
            </span>
            <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Autonomous
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          {/* Active Tasks Counter with direct refresh icon */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>Active Tasks: <strong className="text-white font-mono">{activeTasksCount}</strong></span>
            <button
              onClick={onSyncCalendar}
              disabled={isSyncing}
              className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400 transition ml-1"
              title="Sync & refresh schedule"
            >
              <RefreshCw className={`w-3 h-3 ${isSyncing ? "animate-spin text-cyan-400" : ""}`} />
            </button>
          </div>

          {/* Emergency Reshuffle Button */}
          <button
            onClick={onTriggerReshuffle}
            className="relative group flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 hover:from-amber-400 hover:to-rose-400 text-white text-xs font-semibold shadow-lg shadow-rose-500/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <AlertTriangle className="w-4 h-4 text-white animate-pulse" />
            <span>Emergency Reshuffle</span>
            <div className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
            </div>
          </button>

          {/* User Profile Avatar & Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center space-x-2 p-1.5 pl-2 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition"
              title="User profile and integration settings"
            >
              <div className="relative">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center font-bold text-xs text-white">
                  AD
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 border-2 border-slate-900"></span>
              </div>
              <span className="hidden sm:inline text-xs font-medium text-slate-300">{userName}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {isDropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl bg-slate-900/95 border border-slate-700/80 shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-150 backdrop-blur-xl">
                {/* Account info */}
                <div className="px-3 py-2 border-b border-slate-800">
                  <p className="text-xs font-bold text-white">{userName}</p>
                  <p className="text-[11px] text-slate-400 truncate">{userEmail}</p>
                </div>

                {/* Menu items */}
                <div className="py-1 text-xs">
                  <button
                    onClick={() => {
                      setIsDropdownOpen(false);
                      onOpenSettings();
                    }}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition"
                  >
                    <Settings className="w-4 h-4 text-cyan-400" />
                    <span>Settings & Integrations</span>
                  </button>

                  <button
                    onClick={() => {
                      setIsDropdownOpen(false);
                      onSyncCalendar();
                    }}
                    disabled={isSyncing}
                    className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 text-indigo-400 ${isSyncing ? "animate-spin" : ""}`} />
                    <span>Force Calendar Sync</span>
                  </button>
                </div>

                <div className="pt-1 border-t border-slate-800 px-3 py-1.5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                  <span>Supabase RLS Active</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
