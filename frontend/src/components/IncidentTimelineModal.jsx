import React, { useState, useEffect } from "react";
import {
  X,
  AlertTriangle,
  RotateCcw,
  CheckCircle,
  XCircle,
  Shield,
  Clock,
  Server,
  Layers,
  FileText,
  Key,
  ChevronRight,
  Database
} from "lucide-react";
import { getIncidentDetail, triggerManualRollback } from "../api";

export default function IncidentTimelineModal({ incidentId, onClose, onRefresh }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [rollbackReason, setRollbackReason] = useState("Operator triggered manual backout");
  const [showRollbackConfirm, setShowRollbackConfirm] = useState(false);
  const [rollbackLoading, setRollbackLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("timeline"); // "timeline", "snapshot", "itil"

  useEffect(() => {
    if (!incidentId) return;
    setLoading(true);
    getIncidentDetail(incidentId)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [incidentId]);

  if (!incidentId) return null;

  const handleRollback = async () => {
    setRollbackLoading(true);
    try {
      await triggerManualRollback(incidentId, rollbackReason);
      setShowRollbackConfirm(false);
      onRefresh && onRefresh();
      // Reload detail
      const updated = await getIncidentDetail(incidentId);
      setData(updated);
    } catch (e) {
      alert(`Rollback failed: ${e.message}`);
    } finally {
      setRollbackLoading(false);
    }
  };

  const inc = data?.incident;
  const timeline = data?.timeline || [];
  const change = data?.change_record;
  const explain = data?.explainability;

  const getDecisionBadge = (decision) => {
    switch (decision) {
      case "ALLOW":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">ALLOW (Auto-Remediate)</span>;
      case "REQUIRE_APPROVAL":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">REQUIRE_APPROVAL (Human Review)</span>;
      case "DENY":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30">DENY (Strict Safety Block)</span>;
      case "ESCALATE":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30">ESCALATE (Ambiguity Guard)</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">{decision}</span>;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "RESOLVED":
        return <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"><CheckCircle className="w-3.5 h-3.5" /> RESOLVED</span>;
      case "ROLLED_BACK":
        return <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30"><RotateCcw className="w-3.5 h-3.5" /> ROLLED_BACK</span>;
      case "DENIED":
        return <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30"><XCircle className="w-3.5 h-3.5" /> DENIED</span>;
      case "ESCALATED":
        return <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30"><AlertTriangle className="w-3.5 h-3.5" /> ESCALATED</span>;
      case "PENDING_APPROVAL":
        return <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse"><Clock className="w-3.5 h-3.5" /> PENDING_APPROVAL</span>;
      default:
        return <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">{status}</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="relative flex flex-col w-full max-w-4xl max-h-[90vh] rounded-2xl border border-slate-700/80 bg-night-900 shadow-2xl overflow-hidden">
        
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-night-850">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-bold text-slate-400 bg-night-950 px-2.5 py-1 rounded border border-slate-800">
              {incidentId}
            </span>
            {inc && getStatusBadge(inc.status)}
            {inc && (
              <span className="text-xs font-mono text-slate-400">
                Tier {inc.risk_tier} Risk
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-night-800 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {loading ? (
          <div className="p-16 text-center text-slate-400">Loading incident telemetry...</div>
        ) : inc ? (
          <div className="flex flex-col flex-1 overflow-y-auto p-6 space-y-6">
            
            {/* Title & Metadata */}
            <div>
              <h2 className="text-xl font-bold text-white mb-2">{inc.title}</h2>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Server className="h-3.5 w-3.5 text-cyan-400" /> Host: <strong className="text-slate-200">{inc.host}</strong>
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="h-3.5 w-3.5 text-purple-400" /> Service: <strong className="text-slate-200">{inc.service}</strong>
                </span>
                <span className="flex items-center gap-1">
                  <Key className="h-3.5 w-3.5 text-amber-400" /> Runbook: <strong className="text-slate-200">{inc.runbook_id || "None"}</strong>
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-slate-400" /> Detected: <span className="font-mono">{new Date(inc.created_at).toLocaleTimeString()}</span>
                </span>
              </div>
            </div>

            {/* Explainability Banner: "Why this was decided" */}
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-950/20 p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
                  <Shield className="h-4 w-4" /> Explainability Engine: Decision Rationale
                </span>
                {getDecisionBadge(inc.decision)}
              </div>
              <p className="text-sm text-slate-200 leading-relaxed font-sans">
                {inc.decision_reason || "Decision evaluated against policy engine risk matrix."}
              </p>
              {inc.rollback_reason && (
                <div className="mt-3 pt-3 border-t border-cyan-900/40 text-xs text-amber-300">
                  <strong>Rollback Context:</strong> {inc.rollback_reason}
                </div>
              )}
            </div>

            {/* Sub-Tabs: Timeline / Snapshot / ITIL Change */}
            <div className="flex items-center gap-2 border-b border-slate-800">
              <button
                onClick={() => setActiveTab("timeline")}
                className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${
                  activeTab === "timeline"
                    ? "border-cyan-400 text-cyan-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                Execution Timeline ({timeline.length})
              </button>
              <button
                onClick={() => setActiveTab("snapshot")}
                className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${
                  activeTab === "snapshot"
                    ? "border-cyan-400 text-cyan-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                State Snapshot
              </button>
              <button
                onClick={() => setActiveTab("itil")}
                className={`px-4 py-2 text-sm font-semibold border-b-2 transition-all ${
                  activeTab === "itil"
                    ? "border-cyan-400 text-cyan-400"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                ITIL Change Record {change ? `(${change.id})` : "(None)"}
              </button>
            </div>

            {/* TAB CONTENT: TIMELINE */}
            {activeTab === "timeline" && (
              <div className="relative pl-6 space-y-4 before:absolute before:bottom-2 before:top-2 before:left-2.5 before:w-0.5 before:bg-slate-800">
                {timeline.map((ev, index) => (
                  <div key={ev.id || index} className="relative group">
                    <div className="absolute -left-6 top-1.5 h-3.5 w-3.5 rounded-full border-2 border-night-900 bg-cyan-500 shadow-sm shadow-cyan-500" />
                    <div className="rounded-xl border border-slate-800/80 bg-night-850 p-4 hover:border-slate-700 transition-colors">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-mono font-bold text-cyan-300">
                          {ev.event_type}
                        </span>
                        <span className="text-slate-500 font-mono">
                          {new Date(ev.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2 mb-2">
                        <span>Actor: <strong className="text-slate-300">{ev.actor}</strong></span>
                        <span className="text-slate-600">•</span>
                        <span className="font-mono text-[10px] text-slate-500">Hash: {ev.curr_hash?.slice(0, 10)}...</span>
                      </div>
                      <pre className="text-[11px] font-mono text-slate-300 bg-night-950 p-2.5 rounded-lg overflow-x-auto border border-slate-800/60 max-h-32">
                        {JSON.stringify(ev.payload, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* TAB CONTENT: SNAPSHOT */}
            {activeTab === "snapshot" && (
              <div className="space-y-4">
                <div className="rounded-xl border border-slate-800 bg-night-850 p-4 text-xs text-slate-300">
                  <div className="font-bold text-white mb-1">Atomic Pre-Execution State Snapshot</div>
                  <p className="text-slate-400 mb-3">
                    NightShift captured this exact component state before applying mutations. In case of verification failure, state is restored from this record.
                  </p>
                  <pre className="p-4 rounded-xl bg-night-950 font-mono text-xs text-cyan-300 overflow-x-auto border border-slate-800">
                    {JSON.stringify(inc.snapshot_data, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* TAB CONTENT: ITIL CHANGE RECORD */}
            {activeTab === "itil" && (
              <div className="space-y-4">
                {change ? (
                  <div className="rounded-xl border border-slate-800 bg-night-850 p-5 space-y-4 text-xs">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div>
                        <span className="font-mono font-bold text-sm text-cyan-400">{change.id}</span>
                        <h4 className="text-white font-bold text-base mt-0.5">{change.title}</h4>
                      </div>
                      <span className="px-3 py-1 rounded bg-night-950 text-slate-300 font-mono border border-slate-800">
                        {change.change_type} CHANGE
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-400">
                      <div>
                        <span className="block text-[11px] uppercase tracking-wider text-slate-500">Approver</span>
                        <strong className="text-slate-200">{change.approver_name} ({change.approver_type})</strong>
                      </div>
                      <div>
                        <span className="block text-[11px] uppercase tracking-wider text-slate-500">Execution Result</span>
                        <strong className={change.execution_result === "SUCCESS" ? "text-emerald-400" : "text-amber-400"}>
                          {change.execution_result}
                        </strong>
                      </div>
                      <div>
                        <span className="block text-[11px] uppercase tracking-wider text-slate-500">Duration</span>
                        <strong className="text-slate-200">{change.duration_ms} ms</strong>
                      </div>
                      <div>
                        <span className="block text-[11px] uppercase tracking-wider text-slate-500">Rollback Status</span>
                        <strong className={change.rollback_executed ? "text-amber-400" : "text-slate-400"}>
                          {change.rollback_executed ? "EXECUTED" : "NONE REQUIRED"}
                        </strong>
                      </div>
                    </div>

                    <div>
                      <span className="block text-[11px] uppercase tracking-wider text-slate-500 mb-1">Verification Outcome</span>
                      <p className="p-3 bg-night-950 rounded-lg text-slate-300 font-mono text-[11px] border border-slate-800">
                        {change.verification_outcome}
                      </p>
                    </div>

                    <div>
                      <span className="block text-[11px] uppercase tracking-wider text-slate-500 mb-1">Planned Actions</span>
                      <pre className="p-3 bg-night-950 rounded-lg text-slate-400 font-mono text-[11px] border border-slate-800 max-h-40 overflow-y-auto">
                        {JSON.stringify(change.planned_actions, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="p-12 text-center text-slate-500 text-sm">
                    No ITIL change record generated for this incident (Incident was escalated, denied, or pending).
                  </div>
                )}
              </div>
            )}

            {/* MANUAL ROLLBACK SECTION */}
            {explain?.can_rollback && (
              <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-sm font-bold text-white flex items-center gap-2">
                    <RotateCcw className="h-4 w-4 text-amber-400" /> Manual Backout Control
                  </div>
                  <div className="text-xs text-slate-400">
                    Snapshot is intact. Operator can safely revert target back to pre-incident state.
                  </div>
                </div>
                {!showRollbackConfirm ? (
                  <button
                    onClick={() => setShowRollbackConfirm(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 transition-all"
                  >
                    <RotateCcw className="h-3.5 w-3.5" /> Revert to Snapshot
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={rollbackReason}
                      onChange={(e) => setRollbackReason(e.target.value)}
                      placeholder="Reason for backout..."
                      className="px-3 py-1.5 rounded-lg text-xs bg-night-950 border border-slate-700 text-white"
                    />
                    <button
                      onClick={handleRollback}
                      disabled={rollbackLoading}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-600 text-white hover:bg-amber-500"
                    >
                      {rollbackLoading ? "Reverting..." : "Confirm Rollback"}
                    </button>
                    <button
                      onClick={() => setShowRollbackConfirm(false)}
                      className="px-2 py-1.5 text-xs text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            )}

          </div>
        ) : null}
      </div>
    </div>
  );
}
