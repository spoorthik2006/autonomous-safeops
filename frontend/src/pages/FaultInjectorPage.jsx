import React, { useState } from "react";
import {
  Zap,
  Play,
  RotateCcw,
  AlertTriangle,
  Shield,
  ShieldAlert,
  Flame,
  CheckCircle,
  Clock,
  Sparkles
} from "lucide-react";
import { injectFault, runDemoScenario, resetInfra } from "../api";

export default function FaultInjectorPage({ onRefresh, onSelectIncident }) {
  const [runningDemo, setRunningDemo] = useState(false);
  const [demoProgress, setDemoProgress] = useState(null);
  const [injectingType, setInjectingType] = useState(null);
  const [selectedHost, setSelectedHost] = useState("host-01");
  const [lastResult, setLastResult] = useState(null);

  const handleInject = async (faultType) => {
    setInjectingType(faultType);
    try {
      const res = await injectFault(faultType, selectedHost);
      setLastResult(res);
      onRefresh && onRefresh();
    } catch (err) {
      alert(`Fault injection failed: ${err.message}`);
    } finally {
      setInjectingType(null);
    }
  };

  const handleReset = async () => {
    try {
      await resetInfra();
      setLastResult(null);
      onRefresh && onRefresh();
      alert("Simulated infrastructure sandbox restored to pristine nominal state.");
    } catch (err) {
      alert(`Reset failed: ${err.message}`);
    }
  };

  const handleRunDemo = async () => {
    setRunningDemo(true);
    setDemoProgress("Initializing 10-Fault Demonstration Sequence...");
    try {
      const res = await runDemoScenario();
      setDemoProgress(`Complete! Successfully evaluated ${res.scenario_count} scenarios.`);
      onRefresh && onRefresh();
    } catch (err) {
      setDemoProgress(`Demo encountered error: ${err.message}`);
    } finally {
      setRunningDemo(false);
    }
  };

  return (
    <div className="space-y-6">

      {/* Top Demo Banner */}
      <div className="rounded-2xl border border-cyan-500/40 bg-gradient-to-r from-cyan-950/40 via-night-900 to-purple-950/40 p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
              <Sparkles className="h-4 w-4" /> Automated 10-Fault Showcase
            </div>
            <h2 className="text-2xl font-black text-white">
              Run Complete NightShift Demo Scenario
            </h2>
            <p className="text-sm text-slate-300 max-w-2xl">
              Injects a curated sequence of 10 faults: routine auto-remediations, ambiguous core dumps (escalated), protected /etc (denied), failing fixes (auto-rolled back), and Tier-2 approvals.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleRunDemo}
              disabled={runningDemo}
              className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl font-black text-sm bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-xl shadow-cyan-950/50 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Play className="h-4 w-4 fill-white" />
              {runningDemo ? "Running Scenario..." : "Run 10-Fault Demo"}
            </button>
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-3.5 rounded-xl text-xs font-bold border border-slate-700 bg-night-850 hover:bg-night-800 text-slate-300 transition-colors"
            >
              <RotateCcw className="h-4 w-4" /> Reset Sandbox
            </button>
          </div>
        </div>

        {demoProgress && (
          <div className="mt-4 pt-4 border-t border-cyan-900/40 flex items-center gap-3 text-xs text-cyan-300 font-mono">
            <Clock className="h-4 w-4 animate-spin text-cyan-400" />
            <span>{demoProgress}</span>
          </div>
        )}
      </div>

      {/* Target Host Selector */}
      <div className="flex items-center gap-4 bg-night-900 p-4 rounded-xl border border-slate-800 text-xs">
        <span className="font-bold text-slate-300">Target Host for Manual Injection:</span>
        {["host-01", "host-02", "host-03"].map((h) => (
          <label key={h} className="flex items-center gap-1.5 cursor-pointer text-slate-300">
            <input
              type="radio"
              name="host"
              value={h}
              checked={selectedHost === h}
              onChange={() => setSelectedHost(h)}
              className="text-cyan-500 focus:ring-0"
            />
            <span className="font-mono">{h}</span>
          </label>
        ))}
      </div>

      {/* Fault Injection Categories */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Column 1: Routine Autonomous (Tier 0 & 1) */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
            <CheckCircle className="h-4 w-4" />
            <h3>1. Autonomous Remediations (Tier 0/1)</h3>
          </div>
          <p className="text-xs text-slate-400">
            Safe actions that automatically execute, take pre-check snapshots, mutate, verify, and generate ITIL change records.
          </p>

          <div className="space-y-2.5">
            <button
              onClick={() => handleInject("routine_log_overflow")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-emerald-500/50 hover:bg-emerald-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-emerald-400 transition-colors">
                Routine Log Overflow (/var/log)
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Rotates logs when cause='logs'. Auto-resolves (Tier 0).
              </div>
            </button>

            <button
              onClick={() => handleInject("stuck_worker")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-emerald-500/50 hover:bg-emerald-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-emerald-400 transition-colors">
                Stuck Background Worker
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Deadlocked worker process. Restarts & verifies health (Tier 1).
              </div>
            </button>

            <button
              onClick={() => handleInject("queue_backlog")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-emerald-500/50 hover:bg-emerald-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-emerald-400 transition-colors">
                Queue Consumer Lag
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Backlog &gt; 10k msgs. Scales consumers 2 &rarr; 6 (Tier 1).
              </div>
            </button>

            <button
              onClick={() => handleInject("zombie_leak")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-emerald-500/50 hover:bg-emerald-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-emerald-400 transition-colors">
                Zombie Process Accumulation
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Reaps defunct child processes automatically (Tier 0).
              </div>
            </button>
          </div>
        </div>

        {/* Column 2: Judgment & Ambiguity Guards */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-purple-400 font-bold text-sm">
            <AlertTriangle className="h-4 w-4" />
            <h3>2. Ambiguity Guards & Protected Paths</h3>
          </div>
          <p className="text-xs text-slate-400">
            Never guess. Ambiguous cases escalate to human engineers. Protected paths are strictly denied.
          </p>

          <div className="space-y-2.5">
            <button
              onClick={() => handleInject("ambiguous_disk_full")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-purple-500/50 hover:bg-purple-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-purple-400 transition-colors">
                Ambiguous Disk Spike (Core Dumps)
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Crash dumps in /data/core. Engine refuses to delete &amp; escalates!
              </div>
            </button>

            <button
              onClick={() => handleInject("unknown_disk_full")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-purple-500/50 hover:bg-purple-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-purple-400 transition-colors">
                Unclassified Spike (Low Confidence)
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Root cause unknown. Strict ambiguity guard forces ESCALATE.
              </div>
            </button>

            <button
              onClick={() => handleInject("protected_path_tamper")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-red-500/50 hover:bg-red-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-red-400 transition-colors">
                Protected Surface Tamper (/etc/sudoers)
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Tier 3 protected path. Strictly DENIED by policy engine.
              </div>
            </button>
          </div>
        </div>

        {/* Column 3: Auto-Rollback & Approvals */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
            <RotateCcw className="h-4 w-4" />
            <h3>3. Rollback Failure & Human Approvals</h3>
          </div>
          <p className="text-xs text-slate-400">
            Failing fixes trigger automatic snapshot rollback. Tier 2 actions create human approvals.
          </p>

          <div className="space-y-2.5">
            <button
              onClick={() => handleInject("failed_fix_worker")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-amber-500/50 hover:bg-amber-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-amber-400 transition-colors">
                Remediation Fails &rarr; Automatic Rollback
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Fix fails post-check &rarr; atomically reverts state to snapshot!
              </div>
            </button>

            <button
              onClick={() => handleInject("cert_expiring")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-amber-500/50 hover:bg-amber-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-amber-400 transition-colors">
                Expiring TLS Cert (Tier 2 Approval)
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                SSL cert &lt; 14 days. Queues human approval with rollback plan.
              </div>
            </button>

            <button
              onClick={() => handleInject("service_5xx_spike")}
              disabled={injectingType !== null}
              className="w-full text-left p-3.5 rounded-xl border border-slate-800 bg-night-850 hover:border-amber-500/50 hover:bg-amber-950/10 transition-all group"
            >
              <div className="font-bold text-xs text-white group-hover:text-amber-400 transition-colors">
                API 5xx Spike (Rolling Restart)
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Tier 2 service restart requiring human sign-off.
              </div>
            </button>
          </div>
        </div>

      </div>

      {/* Live Result Output */}
      {lastResult && (
        <div className="rounded-2xl border border-cyan-500/30 bg-night-900 p-5 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-cyan-400 uppercase tracking-wider">
              Fault Injection Telemetry Response
            </span>
            <button
              onClick={() => onSelectIncident(lastResult.incident?.id)}
              className="text-cyan-400 underline font-mono text-xs"
            >
              Open Full Trace: {lastResult.incident?.id} &rarr;
            </button>
          </div>
          <pre className="p-4 rounded-xl bg-night-950 text-xs font-mono text-slate-300 overflow-x-auto border border-slate-800">
            {JSON.stringify(lastResult, null, 2)}
          </pre>
        </div>
      )}

    </div>
  );
}
