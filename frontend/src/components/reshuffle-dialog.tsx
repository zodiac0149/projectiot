"use client";

import React, { useState } from "react";
import { 
  X, 
  AlertTriangle, 
  Cpu, 
  Zap, 
  CheckCircle2, 
  Clock, 
  Sparkles,
  ArrowRight
} from "lucide-react";
import { ReshuffleResponse } from "../types";

interface ReshuffleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onExecuteReshuffle: (disruptionContext: string, horizonDays: number) => Promise<ReshuffleResponse>;
}

const PRESET_DISRUPTIONS = [
  "Embedded systems hardware lab ran 2.5 hours late",
  "Unexpected illness caused loss of morning deep work window",
  "Surprise algorithm quiz scheduled for tomorrow at 09:00",
  "Capstone project group meeting extended by 3 hours",
];

export const ReshuffleDialog: React.FC<ReshuffleDialogProps> = ({
  isOpen,
  onClose,
  onExecuteReshuffle,
}) => {
  const [context, setContext] = useState(PRESET_DISRUPTIONS[0]);
  const [horizonDays, setHorizonDays] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ReshuffleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleTrigger = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await onExecuteReshuffle(context, horizonDays);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Reshuffle optimization failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetAndClose = () => {
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-panel rounded-2xl w-full max-w-xl border border-rose-500/30 shadow-2xl p-6 relative">
        {/* Close Button */}
        <button
          onClick={handleResetAndClose}
          className="absolute top-5 right-5 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <AlertTriangle className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
              <span>Emergency Schedule Reshuffle</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                LLM + Heuristic Fallback
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Dynamically recompute study sessions around unforeseen schedule delays
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/60 border border-rose-800/80 text-xs text-rose-300">
            {error}
          </div>
        )}

        {/* Content View: Input Form or Results Review */}
        {!result ? (
          <div className="space-y-4 text-xs">
            {/* Disruption Context */}
            <div>
              <label className="block text-slate-300 font-medium mb-1.5">
                Disruption Scenario Description
              </label>
              <textarea
                rows={3}
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Describe the delay or commitment change..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-rose-500 transition text-xs"
              />
            </div>

            {/* Quick Presets */}
            <div>
              <span className="block text-[11px] text-slate-400 font-medium mb-2">
                Quick Engineering Presets:
              </span>
              <div className="space-y-1.5">
                {PRESET_DISRUPTIONS.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setContext(preset)}
                    className={`w-full text-left px-3 py-2 rounded-lg border text-xs transition flex items-center justify-between ${
                      context === preset
                        ? "bg-rose-950/40 border-rose-500/50 text-rose-200"
                        : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                    }`}
                  >
                    <span className="truncate">{preset}</span>
                    <ArrowRight className="w-3 h-3 shrink-0 ml-2 opacity-50" />
                  </button>
                ))}
              </div>
            </div>

            {/* Horizon Days */}
            <div className="pt-2">
              <label className="block text-slate-300 font-medium mb-1.5">
                Optimization Horizon: <strong className="text-white">{horizonDays} Days</strong>
              </label>
              <div className="flex space-x-2">
                {[3, 5, 7, 14].map((days) => (
                  <button
                    key={days}
                    type="button"
                    onClick={() => setHorizonDays(days)}
                    className={`flex-1 py-1.5 rounded-lg border text-xs font-semibold transition ${
                      horizonDays === days
                        ? "bg-rose-600 text-white border-rose-500 shadow-md shadow-rose-600/20"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {days} Days
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Action */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={handleResetAndClose}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleTrigger}
                disabled={isLoading}
                className="flex items-center space-x-2 px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-rose-600 hover:from-amber-400 hover:to-rose-500 text-white font-semibold shadow-lg shadow-rose-600/25 transition disabled:opacity-50"
              >
                <Zap className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
                <span>{isLoading ? "Optimizing Temporal Slots..." : "Run Reshuffle Engine"}</span>
              </button>
            </div>
          </div>
        ) : (
          /* Result Summary */
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-200 flex items-start space-x-3">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-sm text-white">Schedule Successfully Reallocated</h4>
                <p className="text-xs text-emerald-300/90 mt-0.5">
                  Precomputed free time windows utilized: <strong className="font-mono">{result.free_slots_found || 0}</strong>.
                  Allocated sessions: <strong className="font-mono">{(result.allocated_sessions || []).length}</strong>.
                </p>
              </div>
            </div>

            {(result.unplaced_task_ids || []).length > 0 && (
              <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-800/60 text-amber-200 text-xs">
                ⚠️ <strong className="font-semibold">{(result.unplaced_task_ids || []).length}</strong> task(s) could not fit before deadline. Consider extending deadlines or reducing estimated hours.
              </div>
            )}

            {/* List of reallocated sessions with rationales */}
            <div>
              <h5 className="font-semibold text-slate-200 mb-2">Reallocated Study Plan:</h5>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {(result.allocated_sessions || []).map((s, idx) => (
                  <div
                    key={s.id || idx}
                    className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center justify-between font-semibold text-white">
                      <span>{s.task_title || "Allocated Session"}</span>
                      <span className="font-mono text-cyan-400 text-[11px]">
                        {s.start_time.slice(11, 16)} - {s.end_time.slice(11, 16)} UTC
                      </span>
                    </div>
                    {s.rationale && (
                      <p className="text-[11px] text-slate-400 mt-1 italic">
                        💡 {s.rationale}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={handleResetAndClose}
                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
              >
                Done & Apply to View
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
