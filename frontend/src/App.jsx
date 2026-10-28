import React, { useState, useEffect, useRef } from "react";
import {
  Shield,
  Power,
  Activity,
  CheckCircle,
  Clock,
  Zap,
  FileCode,
  Database,
  BarChart3,
  Wifi,
  WifiOff,
  AlertTriangle,
  RotateCcw
} from "lucide-react";
import DashboardPage from "./pages/DashboardPage";
import ApprovalsPage from "./pages/ApprovalsPage";
import FaultInjectorPage from "./pages/FaultInjectorPage";
import RunbooksPage from "./pages/RunbooksPage";
import AuditPage from "./pages/AuditPage";
import MetricsPage from "./pages/MetricsPage";
import KillSwitchModal from "./components/KillSwitchModal";
import IncidentTimelineModal from "./components/IncidentTimelineModal";
import {
  getIncidents,
  getApprovals,
  getSafetyStatus,
  toggleKillSwitch,
  getInfraTelemetry,
  getMetrics,
  getWebSocketUrl,
  runBackendTests
} from "./api";

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [incidents, setIncidents] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [safety, setSafety] = useState({ kill_switch_active: false });
  const [infra, setInfra] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [showKillModal, setShowKillModal] = useState(false);
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);

  const wsRef = useRef(null);

  const fetchAllData = async () => {
    try {
      const [incList, apprList, safe, inf, met] = await Promise.all([
        getIncidents(),
        getApprovals(),
        getSafetyStatus(),
        getInfraTelemetry(),
        getMetrics(),
      ]);
      setIncidents(incList);
      setApprovals(apprList);
      setSafety(safe);
      setInfra(inf);
      setMetrics(met);
    } catch (err) {
      console.error("Error fetching NightShift data:", err);
    }
  };

  useEffect(() => {
    fetchAllData();

    // Setup WebSocket
    let ws;
    const connectWs = () => {
      ws = new WebSocket(getWebSocketUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          // Auto-refresh data on events
          if (
            [
              "INCIDENT_DETECTED",
              "INCIDENT_UPDATED",
              "APPROVAL_REQUESTED",
              "APPROVAL_DECIDED",
              "SAFETY_UPDATED",
              "INFRA_RESET"
            ].includes(msg.event)
          ) {
            fetchAllData();
          }
        } catch (_) {}
      };

      ws.onclose = () => {
        setWsConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWs, 3000);
      };

      ws.onerror = () => {
        setWsConnected(false);
      };
    };

    connectWs();

    // Heartbeat ping interval
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 10000);

    return () => {
      clearInterval(pingInterval);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleKillSwitchConfirm = async (active, reason) => {
    await toggleKillSwitch(active, reason);
    await fetchAllData();
  };

  const pendingApprovalsCount = approvals.filter((a) => a.status === "PENDING").length;

  return (
    <div className="min-h-screen bg-night-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      
      {/* GLOBAL HEADER BAR */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-night-900/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          
          {/* Logo & Subtitle */}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 text-white shadow-lg shadow-cyan-950">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-lg text-white tracking-tight">NightShift</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                  AO-04 SAFE OPS
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Policy-Governed Automated Remediation &bull; Rollback Guarantee
              </p>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav className="hidden lg:flex items-center gap-1 bg-night-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === "dashboard"
                  ? "bg-night-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Activity className="h-3.5 w-3.5 text-cyan-400" />
              <span>Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab("approvals")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all relative ${
                activeTab === "approvals"
                  ? "bg-night-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              <span>Approvals</span>
              {pendingApprovalsCount > 0 && (
                <span className="flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[10px] font-mono font-bold text-black animate-pulse">
                  {pendingApprovalsCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("injector")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === "injector"
                  ? "bg-night-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Zap className="h-3.5 w-3.5 text-cyan-400" />
              <span>Fault Injector</span>
            </button>

            <button
              onClick={() => setActiveTab("runbooks")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === "runbooks"
                  ? "bg-night-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <FileCode className="h-3.5 w-3.5 text-purple-400" />
              <span>Runbooks &amp; Policy</span>
            </button>

            <button
              onClick={() => setActiveTab("audit")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === "audit"
                  ? "bg-night-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Database className="h-3.5 w-3.5 text-emerald-400" />
              <span>Audit Ledger</span>
            </button>

            <button
              onClick={() => setActiveTab("metrics")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
                activeTab === "metrics"
                  ? "bg-night-800 text-white shadow-sm border border-slate-700"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <BarChart3 className="h-3.5 w-3.5 text-blue-400" />
              <span>Metrics</span>
            </button>

            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold text-slate-400 hover:text-cyan-400 transition-colors"
              title="Open Swagger OpenAPI Documentation"
            >
              <FileCode className="h-3.5 w-3.5 text-cyan-400" />
              <span>API Docs ↗</span>
            </a>
          </nav>

          {/* Top Right: WebSocket indicator + BIG RED KILL-SWITCH */}
          <div className="flex items-center gap-3">
            
            {/* Real-time WebSocket connection status */}
            <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
              {wsConnected ? (
                <span className="flex items-center gap-1 text-emerald-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="hidden sm:inline">LIVE STREAM</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-slate-500">
                  <WifiOff className="h-3 w-3" />
                  <span className="hidden sm:inline">OFFLINE</span>
                </span>
              )}
            </div>

            {/* BIG RED KILL SWITCH BUTTON */}
            <button
              onClick={() => setShowKillModal(true)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl font-black text-xs uppercase tracking-wider transition-all shadow-lg ${
                safety?.kill_switch_active
                  ? "bg-red-600 hover:bg-red-500 text-white shadow-red-950 border border-red-400 animate-pulse"
                  : "bg-red-950/60 hover:bg-red-900/80 text-red-300 border border-red-500/40 hover:border-red-400"
              }`}
            >
              <Power className="h-4 w-4 shrink-0" />
              <span>
                {safety?.kill_switch_active ? "KILL-SWITCH ACTIVE" : "KILL-SWITCH"}
              </span>
            </button>

          </div>

        </div>

        {/* Mobile Nav */}
        <div className="lg:hidden flex items-center justify-around border-t border-slate-800/80 px-2 py-1 text-xs">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`py-1.5 px-2 ${activeTab === "dashboard" ? "text-cyan-400 font-bold" : "text-slate-400"}`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab("approvals")}
            className={`py-1.5 px-2 ${activeTab === "approvals" ? "text-amber-400 font-bold" : "text-slate-400"}`}
          >
            Approvals ({pendingApprovalsCount})
          </button>
          <button
            onClick={() => setActiveTab("injector")}
            className={`py-1.5 px-2 ${activeTab === "injector" ? "text-cyan-400 font-bold" : "text-slate-400"}`}
          >
            Faults
          </button>
          <button
            onClick={() => setActiveTab("runbooks")}
            className={`py-1.5 px-2 ${activeTab === "runbooks" ? "text-purple-400 font-bold" : "text-slate-400"}`}
          >
            Runbooks
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`py-1.5 px-2 ${activeTab === "audit" ? "text-emerald-400 font-bold" : "text-slate-400"}`}
          >
            Audit
          </button>
          <button
            onClick={() => setActiveTab("metrics")}
            className={`py-1.5 px-2 ${activeTab === "metrics" ? "text-blue-400 font-bold" : "text-slate-400"}`}
          >
            Metrics
          </button>
        </div>
      </header>

      {/* KILL-SWITCH ENGAGED ALERT BANNER */}
      {safety?.kill_switch_active && (
        <div className="bg-red-600 text-white font-bold text-xs py-2 px-4 flex items-center justify-center gap-2 shadow-lg animate-pulse">
          <AlertTriangle className="h-4 w-4" />
          <span>GLOBAL KILL-SWITCH ENGAGED: ALL AUTOMATED REMEDIATIONS ARE CURRENTLY HALTED</span>
          <button
            onClick={() => setShowKillModal(true)}
            className="underline ml-2 hover:text-red-200"
          >
            Click to Disengage
          </button>
        </div>
      )}

      {/* MAIN VIEW CONTENT */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "dashboard" && (
          <DashboardPage
            incidents={incidents}
            metrics={metrics}
            infra={infra}
            onSelectIncident={(id) => setSelectedIncidentId(id)}
            onOpenFaultInjector={() => setActiveTab("injector")}
          />
        )}

        {activeTab === "approvals" && (
          <ApprovalsPage
            approvals={approvals}
            onRefresh={fetchAllData}
            onSelectIncident={(id) => setSelectedIncidentId(id)}
          />
        )}

        {activeTab === "injector" && (
          <FaultInjectorPage
            onRefresh={fetchAllData}
            onSelectIncident={(id) => setSelectedIncidentId(id)}
          />
        )}

        {activeTab === "runbooks" && <RunbooksPage />}

        {activeTab === "audit" && (
          <AuditPage onSelectIncident={(id) => setSelectedIncidentId(id)} />
        )}

        {activeTab === "metrics" && <MetricsPage metrics={metrics} />}
      </main>

      {/* FOOTER */}
      <footer className="border-t border-slate-900 bg-night-950 py-4 text-center text-xs text-slate-500 font-mono">
        NightShift &bull; Problem AO-04 24h Hackathon &bull; Python FastAPI + SQLite + React Vite + SHA-256 Audit Chaining
      </footer>

      {/* MODALS */}
      <KillSwitchModal
        isOpen={showKillModal}
        currentActive={safety?.kill_switch_active}
        onClose={() => setShowKillModal(false)}
        onConfirm={handleKillSwitchConfirm}
      />

      <IncidentTimelineModal
        incidentId={selectedIncidentId}
        onClose={() => setSelectedIncidentId(null)}
        onRefresh={fetchAllData}
      />

    </div>
  );
}
