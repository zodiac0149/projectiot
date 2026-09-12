"use client";

import React, { useState, useEffect, useMemo } from "react";
import { 
  format, 
  addDays, 
  subDays, 
  startOfDay, 
  isSameDay, 
  parseISO, 
  isAfter, 
  isBefore 
} from "date-fns";
import { FixedEvent, StudySession } from "../../types";
import { 
  ShieldCheck, 
  CheckCircle2, 
  Flame, 
  Sparkles,
  Layers,
  ChevronLeft,
  ChevronRight,
  Plus,
  RefreshCw,
  Calendar as CalendarIcon,
  ArrowRight,
  Clock,
  GripVertical
} from "lucide-react";

interface TimelineGridProps {
  fixedEvents: FixedEvent[];
  studySessions: StudySession[];
  onCompleteSession: (sessionId: string) => void;
  onSyncCalendar?: () => Promise<void>;
  isSyncing?: boolean;
  onOpenCreateTask?: (targetDateIso?: string) => void;
  onMoveSessionToDate?: (sessionId: string, targetDate: Date) => void;
}

type ScheduledItem = 
  | { type: "FIXED"; event: FixedEvent; sortPriority: number }
  | { type: "STUDY"; session: StudySession; sortPriority: number };

export const TimelineGrid: React.FC<TimelineGridProps> = ({
  fixedEvents,
  studySessions,
  onCompleteSession,
  onSyncCalendar,
  isSyncing = false,
  onOpenCreateTask,
  onMoveSessionToDate,
}) => {
  // Rolling 3-day window anchor
  const [baseDate, setBaseDate] = useState<Date>(() => startOfDay(new Date()));
  const [dragOverDayIndex, setDragOverDayIndex] = useState<number | null>(null);
  const [draggedSessionId, setDraggedSessionId] = useState<string | null>(null);

  // Auto-advancement at midnight: check system time periodically
  useEffect(() => {
    const checkMidnight = () => {
      const now = startOfDay(new Date());
      // If system date has advanced and user is on current "today", slide forward
      setBaseDate((prev) => {
        const today = startOfDay(new Date());
        return isSameDay(prev, today) ? today : prev;
      });
    };

    const interval = setInterval(checkMidnight, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  // Compute the rolling 3-day window: [baseDate, baseDate + 1, baseDate + 2]
  const days = useMemo(() => {
    return [baseDate, addDays(baseDate, 1), addDays(baseDate, 2)];
  }, [baseDate]);

  const windowEndDay = days[2];

  // The LLM "Disappearing Task" Guardrail: detect sessions scheduled beyond the 3-day window
  const upcomingBeyondWindow = useMemo(() => {
    const cutoff = addDays(windowEndDay, 1); // After Day 3
    return studySessions.filter((s) => {
      try {
        const sDate = parseISO(s.start_time);
        return isAfter(sDate, cutoff);
      } catch {
        return false;
      }
    });
  }, [studySessions, windowEndDay]);

  const getPriorityBadge = (priority: number) => {
    switch (priority) {
      case 5:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-bold shrink-0">
            <Flame className="w-3 h-3 text-rose-400" />
            <span>P5 Critical</span>
          </span>
        );
      case 4:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-300 border border-orange-500/40 text-[10px] font-semibold shrink-0">
            P4 High
          </span>
        );
      case 3:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-semibold shrink-0">
            P3 Medium
          </span>
        );
      case 2:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/40 text-[10px] font-medium shrink-0">
            P2 Review
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-700/80 text-slate-300 text-[10px] font-medium shrink-0">
            P1 Minimal
          </span>
        );
    }
  };

  const handlePrevDay = () => setBaseDate((prev) => subDays(prev, 1));
  const handleNextDay = () => setBaseDate((prev) => addDays(prev, 1));
  const handleResetToday = () => setBaseDate(startOfDay(new Date()));

  const isTodayWindow = isSameDay(baseDate, startOfDay(new Date()));

  return (
    <div className="glass-panel rounded-2xl overflow-hidden shadow-2xl border border-slate-800 flex flex-col h-full w-full">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-6 py-4 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center">
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-center space-x-2">
            <h2 className="text-base font-semibold text-white tracking-tight">
              Day-Wise Plan
            </h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              Rolling 3-Day Window
            </span>
          </div>
        </div>

        {/* Date Navigator Controls */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center bg-slate-950/80 border border-slate-800 rounded-lg p-0.5 text-xs">
            <button
              onClick={handlePrevDay}
              className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Previous Day"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleResetToday}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition ${
                isTodayWindow
                  ? "bg-indigo-600/30 text-indigo-300 font-bold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Today
            </button>
            <button
              onClick={handleNextDay}
              className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Next Day"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Disappearing Task Guardrail Banner (Option B from new.txt) */}
      {upcomingBeyondWindow.length > 0 && (
        <div className="px-6 py-2.5 bg-indigo-950/40 border-b border-indigo-900/50 flex items-center justify-between text-xs text-indigo-200">
          <div className="flex items-center space-x-2">
            <CalendarIcon className="w-3.5 h-3.5 text-cyan-400" />
            <span>
              <strong>{upcomingBeyondWindow.length}</strong> {upcomingBeyondWindow.length === 1 ? "task" : "tasks"} scheduled beyond {format(windowEndDay, "EEEE, MMM d")}
            </span>
          </div>
          <button
            onClick={() => setBaseDate(addDays(windowEndDay, 1))}
            className="flex items-center space-x-1 text-cyan-300 hover:text-cyan-200 font-semibold transition"
          >
            <span>Peek Ahead</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Day Columns Container: 3 Expanded Columns */}
      <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-4 overflow-y-auto max-h-[720px] w-full">
        {days.map((day, dayIndex) => {
          const isToday = isSameDay(day, new Date());

          // Gather fixed events for this day
          const dayFixed: ScheduledItem[] = fixedEvents
            .filter((e) => isSameDay(parseISO(e.start_time), day))
            .map((ev) => ({
              type: "FIXED",
              event: ev,
              sortPriority: 45, // Fixed commitments right below P5 Critical
            }));

          // Gather study sessions for this day (exclude completed or missed sessions)
          const daySessions: ScheduledItem[] = studySessions
            .filter((s) => s.status !== "COMPLETED" && s.status !== "MISSED" && isSameDay(parseISO(s.start_time), day))
            .map((session) => {
              const p = session.task_priority || 3;
              return {
                type: "STUDY",
                session: session,
                sortPriority: p * 10, // P5 = 50 (TOP OF THE DAY), P4 = 40, P3 = 30
              };
            });

          // Combined list sorted strictly in PRIORITY ORDER: HIGHEST PRIORITY AT TOP!
          const sortedItems = [...dayFixed, ...daySessions].sort(
            (a, b) => b.sortPriority - a.sortPriority
          );

          return (
            <div
              key={dayIndex}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOverDayIndex(dayIndex);
              }}
              onDragLeave={() => setDragOverDayIndex(null)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOverDayIndex(null);
                const sId = e.dataTransfer.getData("text/plain") || draggedSessionId;
                if (sId && onMoveSessionToDate) {
                  onMoveSessionToDate(sId, day);
                }
              }}
              className={`rounded-xl border flex flex-col p-4 transition-all min-w-0 w-full overflow-hidden ${
                dragOverDayIndex === dayIndex
                  ? "ring-2 ring-cyan-400 bg-cyan-950/40 border-cyan-400 shadow-xl shadow-cyan-950/50"
                  : isToday
                  ? "bg-slate-900/90 border-indigo-500/50 shadow-lg shadow-indigo-950/30"
                  : "bg-slate-950/50 border-slate-800/90 hover:border-slate-700/80"
              }`}
            >
              {/* Day Header */}
              <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800 min-w-0">
                <div className="min-w-0 pr-1">
                  <div className="flex items-center space-x-1.5 flex-wrap gap-y-0.5">
                    <span className="text-xs uppercase font-bold tracking-wider text-slate-300">
                      {format(day, "EEEE")}
                    </span>
                    {isToday && (
                      <span className="px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shrink-0">
                        Today
                      </span>
                    )}
                  </div>
                  <h4 className="text-sm font-bold text-white mt-0.5">
                    {format(day, "MMM d, yyyy")}
                  </h4>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <span className="text-[11px] font-mono text-slate-400">
                    {sortedItems.length} {sortedItems.length === 1 ? "item" : "items"}
                  </span>
                  {/* Inline quick + button directly on the day column */}
                  {onOpenCreateTask && (
                    <button
                      onClick={() => onOpenCreateTask(day.toISOString())}
                      className="p-1 rounded-md bg-slate-800 hover:bg-indigo-600 text-slate-400 hover:text-white transition"
                      title={`Add task for ${format(day, "MMM d")}`}
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Priority Ordered Card Stack - Highest priority at top */}
              <div className="space-y-3 flex-1 min-w-0">
                {sortedItems.length === 0 ? (
                  <div className="h-44 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700/70 bg-slate-900/30 p-4 text-center transition">
                    <Sparkles className="w-5 h-5 text-indigo-400/70 mb-1.5" />
                    <p className="text-xs text-slate-300 font-medium">
                      No commitments
                    </p>
                    <span className="text-[11px] text-slate-400 mt-0.5">
                      Free self-study window
                    </span>
                  </div>
                ) : (
                  sortedItems.map((item, idx) => {
                    if (item.type === "FIXED") {
                      const ev = item.event;
                      return (
                        <div
                          key={ev.id || `fixed-${idx}`}
                          className="rounded-xl p-3.5 bg-slate-900/90 border border-cyan-600/30 hover:border-cyan-400 shadow-sm transition-all w-full min-w-0 overflow-hidden"
                        >
                          <h5 className="text-xs font-semibold text-slate-100 break-words leading-relaxed">
                            {ev.title}
                          </h5>
                          {/* Subtle time indicator (new.txt spec) */}
                          <div className="flex items-center space-x-1.5 mt-2 text-[10px] text-slate-400 font-mono">
                            <Clock className="w-3 h-3 text-cyan-400 shrink-0" />
                            <span>
                              {format(parseISO(ev.start_time), "h:mm a")} – {format(parseISO(ev.end_time), "h:mm a")}
                            </span>
                          </div>
                        </div>
                      );
                    }

                    // Study Session Item: Single clean priority badge, draggable across day columns
                    const session = item.session;
                    const priority = session.task_priority || 3;
                    const isDone = session.status === "COMPLETED";

                    return (
                      <div
                        key={session.id || `session-${idx}`}
                        draggable={!isDone}
                        onDragStart={(e) => {
                          e.dataTransfer.setData("text/plain", session.id);
                          e.dataTransfer.effectAllowed = "move";
                          setDraggedSessionId(session.id);
                        }}
                        onDragEnd={() => {
                          setDraggedSessionId(null);
                          setDragOverDayIndex(null);
                        }}
                        className={`rounded-xl p-3.5 border shadow-md transition-all w-full min-w-0 overflow-hidden cursor-grab active:cursor-grabbing ${
                          draggedSessionId === session.id
                            ? "opacity-40 scale-95 border-dashed border-cyan-400"
                            : priority === 5
                            ? "bg-rose-950/40 border-rose-500/60 hover:border-rose-400 shadow-rose-950/25"
                            : priority === 4
                            ? "bg-orange-950/30 border-orange-500/50 hover:border-orange-400"
                            : "bg-slate-900/90 border-slate-700/80 hover:border-slate-600"
                        } ${isDone ? "opacity-50 line-through cursor-not-allowed" : ""}`}
                      >
                        {/* Header: Drag handle + single priority tag + complete checkmark */}
                        <div className="flex items-center justify-between mb-2 min-w-0">
                          <div className="flex items-center space-x-1.5 min-w-0">
                            {!isDone && (
                              <GripVertical className="w-3.5 h-3.5 text-slate-500 hover:text-slate-300 shrink-0" />
                            )}
                            {getPriorityBadge(priority)}
                          </div>

                          {!isDone && (
                            <button
                              onClick={() => onCompleteSession(session.id)}
                              className="text-slate-400 hover:text-emerald-400 transition shrink-0 p-0.5"
                              title="Mark session as completed"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>

                        {/* Title */}
                        <h5 className="text-xs font-bold text-white break-words leading-relaxed">
                          {session.task_title || "Allocated Study Block"}
                        </h5>

                        {/* Clean rationale only (no duplicate priority strings) */}
                        {session.rationale && (
                          <div className="mt-2 pt-1.5 border-t border-slate-800/80">
                            <p className="text-[10px] text-slate-400 italic break-words line-clamp-2">
                              💡 {session.rationale
                                .replace(/Priority \d+ deliverable\s*\|\s*/i, "")
                                .replace(/\d+m block\s*\|\s*/i, "")
                                .trim()}
                            </p>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
