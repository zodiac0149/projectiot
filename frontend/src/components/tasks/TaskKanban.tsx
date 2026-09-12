"use client";

import React, { useState } from "react";
import { formatDistanceToNow, parseISO, isPast } from "date-fns";
import { Task } from "../../types";
import { 
  Plus, 
  Trash2, 
  CheckCircle, 
  Clock, 
  Flame, 
  AlertCircle, 
  PlayCircle,
  FolderArchive
} from "lucide-react";

interface TaskKanbanProps {
  tasks: Task[];
  onOpenCreateModal: () => void;
  onUpdateStatus: (taskId: string, newStatus: Task["status"]) => void;
  onDeleteTask: (taskId: string) => void;
}

export const TaskKanban: React.FC<TaskKanbanProps> = ({
  tasks,
  onOpenCreateModal,
  onUpdateStatus,
  onDeleteTask,
}) => {
  const [activeTab, setActiveTab] = useState<"ACTIVE" | "COMPLETED" | "ARCHIVE">("ACTIVE");

  const activeTasks = tasks.filter(
    (t) => (t.status === "PENDING" || t.status === "IN_PROGRESS") && !t.is_deleted && !t.is_expired
  );
  const completedTasks = tasks.filter((t) => t.status === "COMPLETED");
  const archiveTasks = tasks.filter((t) => t.status === "EXPIRED" || t.status === "ARCHIVED" || t.is_expired);

  const currentList =
    activeTab === "ACTIVE"
      ? activeTasks
      : activeTab === "COMPLETED"
      ? completedTasks
      : archiveTasks;

  const getPriorityBadge = (priority: number) => {
    switch (priority) {
      case 5:
        return (
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-bold">
            <Flame className="w-3 h-3 text-rose-400" />
            <span>P5 Critical</span>
          </span>
        );
      case 4:
        return (
          <span className="px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-300 border border-orange-500/40 text-[10px] font-semibold">
            P4 High
          </span>
        );
      case 3:
        return (
          <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-semibold">
            P3 Medium
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-md bg-slate-700 text-slate-300 text-[10px] font-medium">
            P{priority} Low
          </span>
        );
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-5 border border-slate-800 shadow-xl flex flex-col h-full">
      {/* Header and Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Engineering Deliverables</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700 font-mono">
              {tasks.length}
            </span>
          </h3>
        </div>

        <button
          onClick={onOpenCreateModal}
          className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition hover:scale-[1.02] active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          <span>New Task</span>
        </button>
      </div>

      {/* Filter Tabs: Active, Completed, Archive */}
      <div className="flex space-x-2 my-4 p-1 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs">
        <button
          onClick={() => setActiveTab("ACTIVE")}
          className={`flex-1 py-1.5 rounded-lg font-medium transition ${
            activeTab === "ACTIVE"
              ? "bg-slate-800 text-white shadow-sm"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Active ({activeTasks.length})
        </button>
        <button
          onClick={() => setActiveTab("COMPLETED")}
          className={`flex-1 py-1.5 rounded-lg font-medium transition ${
            activeTab === "COMPLETED"
              ? "bg-slate-800 text-white shadow-sm"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Completed ({completedTasks.length})
        </button>
        <button
          onClick={() => setActiveTab("ARCHIVE")}
          className={`flex-1 py-1.5 rounded-lg font-medium transition ${
            activeTab === "ARCHIVE"
              ? "bg-slate-800 text-slate-200 shadow-sm"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Archive ({archiveTasks.length})
        </button>
      </div>

      {/* Task Card List */}
      <div className="space-y-3 overflow-y-auto max-h-[620px] pr-1">
        {currentList.length === 0 ? (
          <div className="text-center py-12 px-4 rounded-xl border border-dashed border-slate-800/80 bg-slate-900/20">
            <FolderArchive className="w-8 h-8 text-slate-600 mx-auto mb-2" />
            <p className="text-xs font-medium text-slate-400">
              No {activeTab.toLowerCase()} tasks in queue.
            </p>
          </div>
        ) : (
          currentList.map((task) => {
            const deadlineDate = parseISO(task.deadline);
            const lapsed = isPast(deadlineDate) && task.status !== "COMPLETED";

            return (
              <div
                key={task.id}
                className="glass-card rounded-xl p-4 border border-slate-800/90 hover:border-slate-700 transition group relative"
              >
                {/* Single clean priority tag */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div>{getPriorityBadge(task.priority)}</div>
                  <span className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{task.estimated_minutes}m</span>
                  </span>
                </div>

                {/* Title and Description */}
                <h4
                  className={`text-sm font-semibold text-slate-100 ${
                    task.status === "COMPLETED" ? "line-through text-slate-500" : ""
                  }`}
                >
                  {task.title}
                </h4>
                {task.description && (
                  <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                    {task.description}
                  </p>
                )}

                {/* Deadline countdown */}
                <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-slate-800/60">
                  <div
                    className={`flex items-center space-x-1 text-[11px] ${
                      lapsed
                        ? "text-rose-400 font-semibold"
                        : "text-slate-400"
                    }`}
                  >
                    {lapsed ? (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                    ) : (
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                    )}
                    <span>
                      {lapsed
                        ? "Deadline lapsed"
                        : `Due ${formatDistanceToNow(deadlineDate, { addSuffix: true })}`}
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-1.5 opacity-90 group-hover:opacity-100 transition">
                    {task.status === "PENDING" && (
                      <button
                        onClick={() => onUpdateStatus(task.id, "IN_PROGRESS")}
                        className="p-1 rounded-md text-slate-400 hover:text-cyan-400 hover:bg-cyan-950/40 transition"
                        title="Mark in progress"
                      >
                        <PlayCircle className="w-4 h-4" />
                      </button>
                    )}

                    {task.status !== "COMPLETED" && (
                      <button
                        onClick={() => onUpdateStatus(task.id, "COMPLETED")}
                        className="p-1 rounded-md text-slate-400 hover:text-emerald-400 hover:bg-emerald-950/40 transition"
                        title="Mark completed"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}

                    <button
                      onClick={() => onDeleteTask(task.id)}
                      className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 transition"
                      title="Soft delete task & invalidate future sessions"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
