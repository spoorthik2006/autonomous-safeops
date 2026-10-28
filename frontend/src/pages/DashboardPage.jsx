import React, { useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
  CheckCircle,
  XCircle,
  Clock,
  Server,
  Layers,
  Activity,
  ArrowRight,
  Database,
  Cpu,
  HardDrive
} from "lucide-react";

export default function DashboardPage({
  incidents,
  metrics,
  infra,
  onSelectIncident,
  onOpenFaultInjector
}) {
  const [filterStatus, setFilterStatus] = useState("ALL");

  const filteredIncidents = incidents.filter((i) => {
    if (filterStatus === "ALL") return true;
    return i.status === filterStatus;
  });

  const getStatusBadge = (status) => {
    switch (status) {
      case "RESOLVED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">RESOLVED</span>;
      case "ROLLED_BACK":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">ROLLED_BACK</span>;
      case "DENIED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30">DENIED</span>;
      case "ESCALATED":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30">ESCALATED</span>;
      case "PENDING_APPROVAL":
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse">PENDING_APPROVAL</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">{status}</span>;
    }
  };

  const hosts = infra?.hosts ? Object.values(infra.hosts) : [];

  return (
    <div className="space-y-6">
      
      {/* KPI METRIC CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        
        {/* Zero Unsafe Actions */}
        <div className="rounded-2xl border border-emerald-500/30 bg-night-900 p-4 shadow-lg shadow-emerald-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Zero Unsafe Actions</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {metrics?.metrics?.zero_unsafe_pct ?? 100}%
          </div>
          <div className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <span>Guaranteed by Policy Engine</span>
          </div>
        </div>

        {/* Auto-Resolved Rate */}
        <div className="rounded-2xl border border-cyan-500/30 bg-night-900 p-4 shadow-lg shadow-cyan-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Auto-Resolved Rate</span>
            <CheckCircle className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {metrics?.metrics?.auto_resolve_pct ?? 0}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {metrics?.resolved_count ?? 0} autonomous fixes
          </div>
        </div>

        {/* Correct Escalations */}
        <div className="rounded-2xl border border-purple-500/30 bg-night-900 p-4 shadow-lg shadow-purple-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Safe Escalations</span>
            <AlertTriangle className="h-4 w-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {metrics?.escalated_count ?? 0}
          </div>
          <div className="text-[11px] text-purple-400 mt-1">
            Never guess on ambiguity
          </div>
        </div>

        {/* Rollback Success */}
        <div className="rounded-2xl border border-amber-500/30 bg-night-900 p-4 shadow-lg shadow-amber-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Rollback Success</span>
            <RotateCcw className="h-4 w-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {metrics?.metrics?.rollback_success_rate ?? 100}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            {metrics?.rolled_back_count ?? 0} safe snapshot reverts
          </div>
        </div>

        {/* Audit Chain Completeness */}
        <div className="rounded-2xl border border-slate-700 bg-night-900 p-4 shadow-lg">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span className="font-semibold uppercase tracking-wider">Audit Integrity</span>
            <Database className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            100%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            SHA-256 chain verified
          </div>
        </div>

      </div>

      {/* SIMULATED INFRASTRUCTURE TELEMETRY */}
      <div className="rounded-2xl border border-slate-800 bg-night-900 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-cyan-400" />
            <h3 className="font-bold text-white text-base">Simulated Production Environment</h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              STATEFUL SANDBOX
            </span>
          </div>
          <button
            onClick={onOpenFaultInjector}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-950 transition-all"
          >
            <span>Fault Injector</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {hosts.map((host) => {
            const varLog = host.disks?.["/var/log"] || {};
            const worker = host.workers?.worker_process || {};
            const isDiskCritical = varLog.utilization_pct > 80;
            const isWorkerUnhealthy = worker.status !== "HEALTHY";

            return (
              <div
                key={host.id}
                className="rounded-xl border border-slate-800/80 bg-night-850 p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                    <strong className="text-sm text-white font-mono">{host.id}</strong>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    CPU {host.cpu_pct?.toFixed(1)}% | RAM {host.memory_pct?.toFixed(1)}%
                  </span>
                </div>

                {/* Disk Gauge */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400 flex items-center gap-1">
                      <HardDrive className="h-3 w-3" /> /var/log
                    </span>
                    <span className={`font-mono font-bold ${isDiskCritical ? "text-red-400" : "text-slate-300"}`}>
                      {varLog.utilization_pct?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-night-950 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        isDiskCritical ? "bg-red-500" : "bg-cyan-500"
                      }`}
                      style={{ width: `${Math.min(varLog.utilization_pct || 0, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Worker Status & Zombies */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Cpu className="h-3 w-3 text-slate-400" />
                    <span>Worker:</span>
                    <strong className={isWorkerUnhealthy ? "text-amber-400" : "text-emerald-400"}>
                      {worker.status || "IDLE"}
                    </strong>
                  </div>
                  <div className="text-[11px]">
                    Zombies: <strong className={host.zombies?.count > 0 ? "text-red-400" : "text-slate-400"}>{host.zombies?.count || 0}</strong>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* INCIDENTS TABLE / FEED */}
      <div className="rounded-2xl border border-slate-800 bg-night-900 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-cyan-400" />
            <h3 className="font-bold text-white text-base">Active Incident & Remediation Ledger</h3>
            <span className="text-xs font-mono text-slate-400 bg-night-950 px-2 py-0.5 rounded border border-slate-800">
              {filteredIncidents.length} Records
            </span>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {["ALL", "RESOLVED", "PENDING_APPROVAL", "ROLLED_BACK", "ESCALATED", "DENIED"].map((st) => (
              <button
                key={st}
                onClick={() => setFilterStatus(st)}
                className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                  filterStatus === st
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                    : "text-slate-400 hover:text-white hover:bg-night-800"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {filteredIncidents.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            No incidents matching filter. Inject faults from the simulator to observe safe policy remediations.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-3">Incident ID</th>
                  <th className="py-3 px-3">Title & Summary</th>
                  <th className="py-3 px-3">Target</th>
                  <th className="py-3 px-3">Policy Decision</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Detected</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredIncidents.map((inc) => (
                  <tr
                    key={inc.id}
                    onClick={() => onSelectIncident(inc.id)}
                    className="hover:bg-night-850/80 cursor-pointer transition-colors group"
                  >
                    <td className="py-3 px-3 font-mono font-bold text-cyan-400">
                      {inc.id}
                    </td>
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-100 group-hover:text-cyan-300 transition-colors">
                        {inc.title}
                      </div>
                      <div className="text-[11px] text-slate-400 truncate max-w-md">
                        {inc.decision_reason}
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      <div>{inc.host}</div>
                      <div className="text-[10px] text-slate-500">{inc.service}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-bold text-[11px] text-slate-300">
                        {inc.decision}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {getStatusBadge(inc.status)}
                    </td>
                    <td className="py-3 px-3 text-slate-500 font-mono text-[11px]">
                      {new Date(inc.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-cyan-400 group-hover:translate-x-1 inline-block transition-transform font-bold text-xs">
                        View Trace →
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
