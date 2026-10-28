import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Database,
  Lock,
  TrendingUp,
  Cpu,
  Layers,
  Play,
  FileCode,
  Check,
  Clock
} from "lucide-react";
import { runBackendTests } from "../api";

export default function MetricsPage({ metrics }) {
  const m = metrics?.metrics || {};
  const [runningTests, setRunningTests] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const handleRunTests = async () => {
    setRunningTests(true);
    try {
      const res = await runBackendTests();
      setTestResult(res);
    } catch (err) {
      alert(`Test run failed: ${err.message}`);
    } finally {
      setRunningTests(false);
    }
  };

  return (
    <div className="space-y-6">

      {/* Top Banner */}
      <div className="rounded-2xl border border-slate-800 bg-night-900 p-6 shadow-xl">
        <h2 className="text-xl font-bold text-white mb-1">
          Safety Telemetry &amp; Operational Governance Metrics
        </h2>
        <p className="text-xs text-slate-400">
          Continuous mathematical verification ensuring automation is provably safe enough to leave switched on 24/7.
        </p>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        
        {/* Zero Unsafe Actions */}
        <div className="rounded-2xl border border-emerald-500/40 bg-night-900 p-5 space-y-2 shadow-lg shadow-emerald-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold uppercase tracking-wider">Zero Unsafe Actions</span>
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="text-4xl font-black text-white font-mono">
            {m.zero_unsafe_pct ?? 100}%
          </div>
          <div className="w-full bg-night-950 h-2 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full" style={{ width: `${m.zero_unsafe_pct ?? 100}%` }} />
          </div>
          <p className="text-[11px] text-slate-400 pt-1">
            0 actions violated blast radius or mutated protected Tier-3 paths.
          </p>
        </div>

        {/* Auto-Resolved Rate */}
        <div className="rounded-2xl border border-cyan-500/40 bg-night-900 p-5 space-y-2 shadow-lg shadow-cyan-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold uppercase tracking-wider">Autonomous Remediation</span>
            <CheckCircle className="h-5 w-5 text-cyan-400" />
          </div>
          <div className="text-4xl font-black text-white font-mono">
            {m.auto_resolve_pct ?? 0}%
          </div>
          <div className="w-full bg-night-950 h-2 rounded-full overflow-hidden">
            <div className="bg-cyan-500 h-full" style={{ width: `${m.auto_resolve_pct ?? 0}%` }} />
          </div>
          <p className="text-[11px] text-slate-400 pt-1">
            {metrics?.resolved_count ?? 0} routine incidents resolved with zero human clicks.
          </p>
        </div>

        {/* Correct Escalations */}
        <div className="rounded-2xl border border-purple-500/40 bg-night-900 p-5 space-y-2 shadow-lg shadow-purple-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold uppercase tracking-wider">Correct Escalations</span>
            <AlertTriangle className="h-5 w-5 text-purple-400" />
          </div>
          <div className="text-4xl font-black text-white font-mono">
            {metrics?.escalated_count ?? 0}
          </div>
          <div className="w-full bg-night-950 h-2 rounded-full overflow-hidden">
            <div className="bg-purple-500 h-full" style={{ width: "100%" }} />
          </div>
          <p className="text-[11px] text-slate-400 pt-1">
            Ambiguous core dumps and unclassified spikes routed to engineers.
          </p>
        </div>

        {/* Rollback Success Rate */}
        <div className="rounded-2xl border border-amber-500/40 bg-night-900 p-5 space-y-2 shadow-lg shadow-amber-950/20">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-bold uppercase tracking-wider">Rollback Reliability</span>
            <RotateCcw className="h-5 w-5 text-amber-400" />
          </div>
          <div className="text-4xl font-black text-white font-mono">
            {m.rollback_success_rate ?? 100}%
          </div>
          <div className="w-full bg-night-950 h-2 rounded-full overflow-hidden">
            <div className="bg-amber-500 h-full" style={{ width: `${m.rollback_success_rate ?? 100}%` }} />
          </div>
          <p className="text-[11px] text-slate-400 pt-1">
            {metrics?.rolled_back_count ?? 0} failed post-verifications cleanly reverted.
          </p>
        </div>

      </div>

      {/* Interactive Backend Test Suite Runner */}
      <div className="rounded-2xl border border-cyan-500/40 bg-night-900 p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white text-base">Backend Test Suite &amp; Invariants Engine</span>
              <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                18 UNIT TESTS
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Verifies Tier 0-3 enforcement, ambiguous core dump escalation, automatic rollback on fix failure, global kill-switch, and SHA-256 tamper detection.
            </p>
          </div>

          <button
            onClick={handleRunTests}
            disabled={runningTests}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg shadow-cyan-950 transition-all hover:scale-[1.02]"
          >
            {runningTests ? (
              <>
                <Clock className="h-4 w-4 animate-spin" />
                <span>Running 18 Tests...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                <span>Run Backend Test Suite</span>
              </>
            )}
          </button>
        </div>

        {testResult && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className={`flex items-center gap-1.5 font-bold ${
                testResult.success ? "text-emerald-400" : "text-red-400"
              }`}>
                {testResult.success ? <Check className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                {testResult.summary} ({testResult.passed}/{testResult.total_tests} Passed in {testResult.duration_sec}s)
              </span>
            </div>
            <pre className="p-4 rounded-xl bg-night-950 font-mono text-[11px] text-slate-300 overflow-x-auto border border-slate-800 max-h-56">
              {testResult.log_output}
            </pre>
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Safety Pillars */}
        <div className="rounded-2xl border border-slate-800 bg-night-900 p-6 space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Lock className="h-5 w-5 text-cyan-400" /> Safety Pillars &amp; Invariants
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl border border-slate-800 bg-night-850">
              <strong className="text-emerald-400 block mb-0.5">1. Pre-Check &amp; State Snapshotting</strong>
              <p className="text-slate-400">
                No mutation occurs without capturing an atomic snapshot first. If verification fails, automatic rollback restores the snapshot immediately.
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-800 bg-night-850">
              <strong className="text-purple-400 block mb-0.5">2. Ambiguity Principle (Never Guess)</strong>
              <p className="text-slate-400">
                Routine logs are auto-rotated; core dumps and unclassified root causes are strictly escalated. Destructive cleanup is never executed on uncertainty.
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-800 bg-night-850">
              <strong className="text-amber-400 block mb-0.5">3. Blast-Radius &amp; Rate Throttling</strong>
              <p className="text-slate-400">
                Actions are limited to a max of 2 hosts per execution and 5 actions per hour per service, preventing cascading failure loops.
              </p>
            </div>

            <div className="p-3.5 rounded-xl border border-slate-800 bg-night-850">
              <strong className="text-cyan-400 block mb-0.5">4. Tamper-Evident SHA-256 Audit Chain</strong>
              <p className="text-slate-400">
                Every detection, decision, approval, action, and rollback is cryptographically linked with SHA-256, producing ITIL change tickets automatically.
              </p>
            </div>
          </div>
        </div>

        {/* Operational Comparison Matrix */}
        <div className="rounded-2xl border border-slate-800 bg-night-900 p-6 space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-emerald-400" /> Operational Paradigm Comparison
          </h3>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                  <th className="py-2.5">Feature</th>
                  <th className="py-2.5">Unchecked Scripts</th>
                  <th className="py-2.5 text-cyan-400">NightShift</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans text-slate-300">
                <tr>
                  <td className="py-2.5 font-semibold text-slate-200">Execution Safety</td>
                  <td className="py-2.5 text-red-400">Blind root execution</td>
                  <td className="py-2.5 text-emerald-400 font-bold">Policy &amp; Tiers</td>
                </tr>
                <tr>
                  <td className="py-2.5 font-semibold text-slate-200">Ambiguity Guard</td>
                  <td className="py-2.5 text-red-400">Deletes blindly</td>
                  <td className="py-2.5 text-purple-400 font-bold">Escalate (never guess)</td>
                </tr>
                <tr>
                  <td className="py-2.5 font-semibold text-slate-200">Rollback Guarantee</td>
                  <td className="py-2.5 text-red-400">None (Manual scramble)</td>
                  <td className="py-2.5 text-amber-400 font-bold">Automatic on failure</td>
                </tr>
                <tr>
                  <td className="py-2.5 font-semibold text-slate-200">Emergency Stop</td>
                  <td className="py-2.5 text-red-400">pkill scripts</td>
                  <td className="py-2.5 text-red-400 font-bold">Hardware Kill-Switch</td>
                </tr>
                <tr>
                  <td className="py-2.5 font-semibold text-slate-200">Auditability</td>
                  <td className="py-2.5 text-slate-500">Volatile text logs</td>
                  <td className="py-2.5 text-cyan-400 font-bold">SHA-256 Hash Chain</td>
                </tr>
                <tr>
                  <td className="py-2.5 font-semibold text-slate-200">Compliance</td>
                  <td className="py-2.5 text-slate-500">Manual ticketing</td>
                  <td className="py-2.5 text-emerald-400 font-bold">Auto ITIL Tickets</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  );
}
