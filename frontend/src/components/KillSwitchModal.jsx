import React, { useState } from "react";
import { AlertTriangle, Power, ShieldAlert } from "lucide-react";

export default function KillSwitchModal({ isOpen, currentActive, onClose, onConfirm }) {
  const [reason, setReason] = useState(
    currentActive
      ? "Manual operator re-engagement after safety verification"
      : "Emergency operator intervention: halt all automated actions"
  );
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onConfirm(!currentActive, reason);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg rounded-2xl border border-red-500/40 bg-night-900 p-6 shadow-2xl shadow-red-950/50">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-red-500/10 text-red-400 border border-red-500/30 animate-pulse">
            <Power className="h-8 w-8" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              {currentActive ? "Disengage Global Kill-Switch" : "ENGAGE GLOBAL KILL-SWITCH"}
            </h3>
            <p className="text-sm text-slate-400">
              {currentActive
                ? "Resumes autonomous policy engine and remediation execution."
                : "IMMEDIATELY stops all automated execution across all hosts and services."}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
              Action Justification / Audit Reason
            </label>
            <textarea
              required
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-night-950 px-4 py-3 text-sm text-white focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              placeholder="State reason for engaging or disengaging the kill switch..."
            />
          </div>

          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-3.5 text-xs text-red-300 flex items-start gap-2.5">
            <ShieldAlert className="h-5 w-5 shrink-0 text-red-400 mt-0.5" />
            <div>
              <span className="font-semibold">Cryptographic Audit Notice:</span> This action is recorded in the append-only SHA-256 ledger with operator identity and immutable timestamp.
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="rounded-xl border border-slate-700 bg-night-800 px-4 py-2.5 text-sm font-semibold text-slate-300 hover:bg-night-750 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold shadow-lg transition-all ${
                currentActive
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30"
                  : "bg-red-600 hover:bg-red-500 text-white shadow-red-900/50"
              }`}
            >
              <Power className="h-4 w-4" />
              {loading
                ? "Executing..."
                : currentActive
                ? "Disengage & Resume Automation"
                : "CONFIRM: ENGAGE KILL-SWITCH"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
