"use client";

import React, { useState } from "react";
import { X, Sparkles, AlertCircle } from "lucide-react";
import { CognitiveLoad, Task } from "../../types";

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateTask: (taskData: Partial<Task>) => Promise<void>;
  initialDateIso?: string;
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({
  isOpen,
  onClose,
  onCreateTask,
  initialDateIso,
}) => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<number>(4);
  const [estimatedMinutes, setEstimatedMinutes] = useState<number>(90);
  const [cognitiveLoad, setCognitiveLoad] = useState<CognitiveLoad>("HIGH");

  // Default deadline: target date or 2 days from now at 23:59
  const computeDeadline = (dateIso?: string) => {
    const d = dateIso ? new Date(dateIso) : new Date();
    if (!dateIso) d.setDate(d.getDate() + 2);
    d.setHours(23, 59, 0, 0);
    return d.toISOString().slice(0, 16);
  };

  const [deadline, setDeadline] = useState(() => computeDeadline(initialDateIso));

  React.useEffect(() => {
    if (isOpen) {
      setDeadline(computeDeadline(initialDateIso));
    }
  }, [isOpen, initialDateIso]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Task title is required.");
      return;
    }
    if (estimatedMinutes <= 0) {
      setError("Estimated study time must be greater than 0.");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onCreateTask({
        title: title.trim(),
        description: description.trim(),
        priority,
        estimated_minutes: Number(estimatedMinutes),
        deadline: new Date(deadline).toISOString(),
        cognitive_load: cognitiveLoad,
        status: "PENDING",
      });
      onClose();
      // Reset form
      setTitle("");
      setDescription("");
      setPriority(4);
      setEstimatedMinutes(90);
      setCognitiveLoad("HIGH");
    } catch (err: any) {
      setError(err.message || "Failed to create task");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel rounded-2xl w-full max-w-lg border border-slate-700 shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2.5 mb-5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Create Engineering Deliverable
            </h3>
            <p className="text-xs text-slate-400">Add an academic milestone to the scheduler queue</p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Title */}
          <div>
            <label className="block text-slate-300 font-medium mb-1.5">
              Task Title <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g., Kernel Module Synchronization Lab"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-slate-300 font-medium mb-1.5">
              Description & Objectives
            </label>
            <textarea
              rows={2}
              placeholder="e.g., Implement spinlocks and atomic primitives for the assignment."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>

          {/* Priority & Cognitive Load */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Priority Level (1 - 5)
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value={5}>5 - Critical (Exams / Deadlines)</option>
                <option value={4}>4 - High (Major Projects)</option>
                <option value={3}>3 - Medium (Regular Homework)</option>
                <option value={2}>2 - Low (Reading / Review)</option>
                <option value={1}>1 - Minimal</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Cognitive Intensity
              </label>
              <select
                value={cognitiveLoad}
                onChange={(e) => setCognitiveLoad(e.target.value as CognitiveLoad)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 transition"
              >
                <option value="HIGH">High (Deep Math / Algorithmic)</option>
                <option value="MEDIUM">Medium (Writing / Coding)</option>
                <option value="LOW">Low (Admin / Reading)</option>
              </select>
            </div>
          </div>

          {/* Duration & Deadline */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Estimated Duration (mins)
              </label>
              <input
                type="number"
                min={15}
                step={15}
                required
                value={estimatedMinutes}
                onChange={(e) => setEstimatedMinutes(Number(e.target.value))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 transition"
              />
              <p className="text-[10px] text-slate-400 mt-1">
                Tasks &gt; 90m will auto-split with breaks
              </p>
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Hard Deadline (UTC)
              </label>
              <input
                type="datetime-local"
                required
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-indigo-500 transition"
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Save Task"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
