import React, { useState, useEffect } from "react";
import {
  Database,
  CheckCircle,
  XCircle,
  Download,
  Search,
  Filter,
  FileText,
  ShieldCheck,
  RefreshCw,
  ExternalLink
} from "lucide-react";
import {
  getAuditEvents,
  verifyAuditChain,
  getChangeRecords,
  getExportJsonUrl,
  getExportCsvUrl
} from "../api";

export default function AuditPage({ onSelectIncident }) {
  const [activeTab, setActiveTab] = useState("audit"); // "audit" or "changes"
  const [events, setEvents] = useState([]);
  const [changes, setChanges] = useState([]);
  const [verification, setVerification] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [filterType, setFilterType] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    Promise.all([getAuditEvents(), verifyAuditChain(), getChangeRecords()])
      .then(([evList, verif, chgList]) => {
        setEvents(evList);
        setVerification(verif);
        setChanges(chgList);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await verifyAuditChain();
      setVerification(res);
    } catch (e) {
      alert(`Verification failed: ${e.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const filteredEvents = events.filter((e) => {
    if (filterType && e.event_type !== filterType) return false;
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const matchId = e.incident_id?.toLowerCase().includes(term);
      const matchType = e.event_type?.toLowerCase().includes(term);
      const matchActor = e.actor?.toLowerCase().includes(term);
      const matchPayload = JSON.stringify(e.payload).toLowerCase().includes(term);
      return matchId || matchType || matchActor || matchPayload;
    }
    return true;
  });

  return (
    <div className="space-y-6">

      {/* Top Banner with Verification Badge */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-night-900 p-6 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Database className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-3">
              Immutable SHA-256 Audit Ledger &amp; Change Records
              {verification?.valid ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  <ShieldCheck className="h-4 w-4" /> Cryptographic Chain Valid ({verification.total_events} Blocks)
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30">
                  <XCircle className="h-4 w-4" /> Integrity Broken at #{verification?.broken_at_id}
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Append-only cryptographic hash chain linking detected alerts, policy decisions, approvals, state snapshots, actions, verifications, and rollbacks.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border border-slate-700 bg-night-850 hover:bg-night-800 text-slate-200 transition-colors"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${verifying ? "animate-spin" : ""}`} />
            <span>Verify Chain</span>
          </button>
          <a
            href={getExportJsonUrl()}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border border-cyan-500/30 bg-cyan-950/20 text-cyan-300 hover:bg-cyan-950/40 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export JSON</span>
          </a>
          <a
            href={getExportCsvUrl()}
            download="nightshift_audit_ledger.csv"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border border-cyan-500/30 bg-cyan-950/20 text-cyan-300 hover:bg-cyan-950/40 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("audit")}
          className={`pb-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "audit"
              ? "border-cyan-400 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Database className="h-4 w-4" />
          <span>Audit Event Ledger ({filteredEvents.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("changes")}
          className={`pb-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "changes"
              ? "border-cyan-400 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>ITIL Standard Change Tickets ({changes.length})</span>
        </button>
      </div>

      {/* TAB 1: AUDIT EVENT LEDGER */}
      {activeTab === "audit" && (
        <div className="space-y-4">
          
          {/* Filters & Search */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-night-900 p-4 rounded-xl border border-slate-800 text-xs">
            <div className="flex items-center gap-2 w-full md:w-auto">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search event type, incident, payload..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="bg-night-950 px-3 py-1.5 rounded-lg text-white border border-slate-800 focus:outline-none focus:border-cyan-500 w-64"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-slate-400">Filter Event:</span>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-night-950 px-3 py-1.5 rounded-lg text-white border border-slate-800 focus:outline-none focus:border-cyan-500 text-xs font-mono"
              >
                <option value="">All Event Types</option>
                <option value="INCIDENT_DETECTED">INCIDENT_DETECTED</option>
                <option value="POLICY_EVALUATED">POLICY_EVALUATED</option>
                <option value="APPROVAL_REQUESTED">APPROVAL_REQUESTED</option>
                <option value="APPROVAL_DECIDED">APPROVAL_DECIDED</option>
                <option value="PRE_CHECK">PRE_CHECK</option>
                <option value="SNAPSHOT_TAKEN">SNAPSHOT_TAKEN</option>
                <option value="ACTION_EXECUTED">ACTION_EXECUTED</option>
                <option value="VERIFICATION_PASSED">VERIFICATION_PASSED</option>
                <option value="VERIFICATION_FAILED">VERIFICATION_FAILED</option>
                <option value="ROLLBACK_INITIATED">ROLLBACK_INITIATED</option>
                <option value="ROLLBACK_COMPLETED">ROLLBACK_COMPLETED</option>
                <option value="KILL_SWITCH_ENGAGED">KILL_SWITCH_ENGAGED</option>
                <option value="KILL_SWITCH_DISENGAGED">KILL_SWITCH_DISENGAGED</option>
              </select>
            </div>
          </div>

          {/* Events Table */}
          <div className="rounded-2xl border border-slate-800 bg-night-900 p-5 overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-3">#</th>
                  <th className="py-3 px-3">Timestamp</th>
                  <th className="py-3 px-3">Event Type</th>
                  <th className="py-3 px-3">Linked Incident</th>
                  <th className="py-3 px-3">Actor</th>
                  <th className="py-3 px-3">Prev Hash &rarr; Curr Hash</th>
                  <th className="py-3 px-3">Payload Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-sans">
                {filteredEvents.map((ev) => (
                  <tr key={ev.id} className="hover:bg-night-850/80 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-slate-500">
                      {ev.id}
                    </td>
                    <td className="py-3 px-3 font-mono text-[11px] text-slate-400">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-3 px-3">
                      <span className="font-mono font-bold text-cyan-300 bg-cyan-950/20 px-2 py-0.5 rounded border border-cyan-500/20">
                        {ev.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      {ev.incident_id ? (
                        <button
                          onClick={() => onSelectIncident(ev.incident_id)}
                          className="font-mono text-cyan-400 hover:underline"
                        >
                          {ev.incident_id}
                        </button>
                      ) : (
                        <span className="text-slate-600 font-mono">-</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300 font-mono text-[11px]">
                      {ev.actor}
                    </td>
                    <td className="py-3 px-3 font-mono text-[10px] text-slate-500">
                      <div>P: {ev.prev_hash?.slice(0, 8)}...</div>
                      <div className="text-cyan-400">C: {ev.curr_hash?.slice(0, 8)}...</div>
                    </td>
                    <td className="py-3 px-3">
                      <pre className="text-[10px] font-mono text-slate-400 bg-night-950 p-1.5 rounded max-w-xs truncate border border-slate-800/60">
                        {JSON.stringify(ev.payload)}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>
      )}

      {/* TAB 2: ITIL CHANGE RECORDS */}
      {activeTab === "changes" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {changes.map((chg) => (
              <div
                key={chg.id}
                className="rounded-2xl border border-slate-800 bg-night-900 p-5 space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-sm text-cyan-400 bg-night-950 px-2.5 py-1 rounded border border-slate-800">
                      {chg.id}
                    </span>
                    <button
                      onClick={() => onSelectIncident(chg.incident_id)}
                      className="font-mono text-xs text-slate-400 hover:text-cyan-300 underline"
                    >
                      Ref: {chg.incident_id}
                    </button>
                    <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-slate-800 text-slate-300 font-mono">
                      {chg.change_type} CHANGE
                    </span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    chg.execution_result === "SUCCESS"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                  }`}>
                    {chg.execution_result}
                  </span>
                </div>

                <div className="text-sm font-bold text-white">{chg.title}</div>
                <div className="text-xs text-slate-400">Trigger: {chg.trigger_reason}</div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs bg-night-850 p-3 rounded-xl border border-slate-800/80">
                  <div>
                    <span className="text-[11px] text-slate-500 block uppercase">Approver</span>
                    <strong className="text-slate-200">{chg.approver_name}</strong>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block uppercase">Duration</span>
                    <strong className="text-slate-200">{chg.duration_ms} ms</strong>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block uppercase">Rollback Status</span>
                    <strong className={chg.rollback_executed ? "text-amber-400" : "text-slate-400"}>
                      {chg.rollback_executed ? "EXECUTED" : "NONE"}
                    </strong>
                  </div>
                  <div>
                    <span className="text-[11px] text-slate-500 block uppercase">Timestamp</span>
                    <span className="font-mono text-slate-400">{new Date(chg.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>

                <div className="text-xs text-slate-300 font-mono bg-night-950 p-3 rounded-xl border border-slate-800">
                  <strong>Verification:</strong> {chg.verification_outcome}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
