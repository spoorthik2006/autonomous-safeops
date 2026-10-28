import React, { useState } from "react";
import {
  Clock,
  CheckCircle,
  XCircle,
  ShieldAlert,
  Server,
  Layers,
  FileText,
  RotateCcw,
  UserCheck
} from "lucide-react";
import { decideApproval } from "../api";

export default function ApprovalsPage({
  approvals,
  onRefresh,
  onSelectIncident
}) {
  const [activeTab, setActiveTab] = useState("PENDING"); // "PENDING" or "DECIDED"
  const [approverName, setApproverName] = useState("ops-lead");
  const [rationales, setRationales] = useState({});
  const [processingId, setProcessingId] = useState(null);

  const pendingApprovals = approvals.filter((a) => a.status === "PENDING");
  const decidedApprovals = approvals.filter((a) => a.status !== "PENDING");
  const currentList = activeTab === "PENDING" ? pendingApprovals : decidedApprovals;

  const handleDecision = async (approvalId, decision) => {
    setProcessingId(approvalId);
    try {
      const rationale = rationales[approvalId] || (
        decision === "APPROVE"
          ? "Approved after verifying blast radius and rollback plan"
          : "Rejected: operational risk too high during business hours"
      );
      await decideApproval(approvalId, decision, approverName, rationale);
      onRefresh && onRefresh();
    } catch (err) {
      alert(`Approval decision failed: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Tier 2 Human Control Point Queue
              <span className="px-2 py-0.5 rounded-full text-xs bg-amber-500/20 text-amber-300 font-mono">
                {pendingApprovals.length} Pending
              </span>
            </h2>
            <p className="text-xs text-slate-300">
              High-impact operational changes requiring human sign-off. The policy engine prepares the execution plan and rollback contract.
            </p>
          </div>
        </div>

        {/* Global Approver Name Input */}
        <div className="flex items-center gap-2 bg-night-900 px-3 py-2 rounded-xl border border-slate-700 text-xs">
          <UserCheck className="h-4 w-4 text-cyan-400" />
          <span className="text-slate-400">Operator:</span>
          <input
            type="text"
            value={approverName}
            onChange={(e) => setApproverName(e.target.value)}
            className="bg-night-950 px-2 py-1 rounded text-white font-mono text-xs border border-slate-800 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("PENDING")}
          className={`pb-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "PENDING"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <span>Pending Approvals</span>
          <span className="px-2 py-0.5 rounded-full text-xs bg-amber-500/10 text-amber-400">
            {pendingApprovals.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("DECIDED")}
          className={`pb-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "DECIDED"
              ? "border-cyan-400 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <span>Historical Decisions</span>
          <span className="px-2 py-0.5 rounded-full text-xs bg-slate-800 text-slate-400">
            {decidedApprovals.length}
          </span>
        </button>
      </div>

      {/* Approvals List */}
      {currentList.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-night-900 p-16 text-center text-slate-500 text-sm">
          {activeTab === "PENDING"
            ? "No approvals pending. All actions are either autonomously resolved or safe."
            : "No decided approvals found."}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5">
          {currentList.map((appr) => {
            const isPending = appr.status === "PENDING";
            const isBusy = processingId === appr.id;

            return (
              <div
                key={appr.id}
                className="rounded-2xl border border-slate-800 bg-night-900 p-6 space-y-4 hover:border-slate-700 transition-colors shadow-xl"
              >
                {/* Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs font-bold text-cyan-400 bg-night-950 px-2.5 py-1 rounded border border-slate-800">
                      {appr.id}
                    </span>
                    <button
                      onClick={() => onSelectIncident(appr.incident_id)}
                      className="font-mono text-xs text-slate-400 hover:text-cyan-400 underline"
                    >
                      Linked: {appr.incident_id}
                    </button>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      Tier {appr.risk_tier} Action
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className={`px-3 py-1 rounded-full font-bold ${
                      appr.status === "APPROVED"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : appr.status === "REJECTED"
                        ? "bg-red-500/10 text-red-400 border border-red-500/30"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse"
                    }`}>
                      {appr.status}
                    </span>
                  </div>
                </div>

                {/* Proposed Action Title */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">{appr.proposed_action}</h3>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Server className="h-3.5 w-3.5 text-cyan-400" /> Host: <strong className="text-slate-200">{appr.host}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <Layers className="h-3.5 w-3.5 text-purple-400" /> Service: <strong className="text-slate-200">{appr.service}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-slate-400" /> Requested: {new Date(appr.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                {/* Blast Radius & Rollback Contract */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="rounded-xl border border-slate-800 bg-night-850 p-3.5 space-y-1">
                    <div className="font-bold text-slate-300 flex items-center gap-1.5">
                      <ShieldAlert className="h-4 w-4 text-amber-400" /> Blast Radius Bound
                    </div>
                    <p className="text-slate-400 leading-relaxed">
                      {appr.blast_radius_summary || "Scoped to 1 host and single service replica."}
                    </p>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-night-850 p-3.5 space-y-1">
                    <div className="font-bold text-slate-300 flex items-center gap-1.5">
                      <RotateCcw className="h-4 w-4 text-cyan-400" /> Verified Rollback Plan
                    </div>
                    <p className="text-slate-400 leading-relaxed">
                      {appr.rollback_plan_summary || "Pre-action snapshot is armed. Automatic reversion triggers if verification fails."}
                    </p>
                  </div>
                </div>

                {/* Proposed Action Steps */}
                {appr.action_steps && appr.action_steps.length > 0 && (
                  <div className="rounded-xl border border-slate-800/60 bg-night-950 p-3.5 space-y-2">
                    <div className="text-xs font-bold text-slate-300">
                      Planned Steps ({appr.action_steps.length})
                    </div>
                    <div className="space-y-1 text-xs">
                      {appr.action_steps.map((st, i) => (
                        <div key={i} className="flex items-center gap-2 text-slate-400">
                          <span className="font-mono text-cyan-400">0{st.step}.</span>
                          <span>{st.name}</span>
                          <span className="text-[10px] font-mono text-slate-600">[{st.action} on {st.target}]</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Decision Area (If Pending) */}
                {isPending && (
                  <div className="pt-3 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-3">
                    <input
                      type="text"
                      placeholder="Add approval / rejection rationale for the audit chain..."
                      value={rationales[appr.id] || ""}
                      onChange={(e) =>
                        setRationales({ ...rationales, [appr.id]: e.target.value })
                      }
                      className="w-full md:w-2/3 px-3.5 py-2 rounded-xl bg-night-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-cyan-500"
                    />

                    <div className="flex items-center gap-2 w-full md:w-auto justify-end">
                      <button
                        onClick={() => handleDecision(appr.id, "REJECT")}
                        disabled={isBusy}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold border border-red-500/40 text-red-400 hover:bg-red-500/10 transition-colors"
                      >
                        <XCircle className="h-4 w-4" /> Reject
                      </button>
                      <button
                        onClick={() => handleDecision(appr.id, "APPROVE")}
                        disabled={isBusy}
                        className="flex items-center gap-1.5 px-5 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-950 transition-all"
                      >
                        <CheckCircle className="h-4 w-4" />
                        {isBusy ? "Executing..." : "Approve & Execute"}
                      </button>
                    </div>
                  </div>
                )}

                {/* If already decided */}
                {!isPending && (
                  <div className="pt-2 text-xs text-slate-400 flex items-center justify-between">
                    <div>
                      Decided by <strong className="text-slate-200">{appr.approver}</strong>: {appr.approval_rationale || appr.rejection_reason || "Signed"}
                    </div>
                    <div className="font-mono text-slate-500">
                      {new Date(appr.decided_at || appr.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
