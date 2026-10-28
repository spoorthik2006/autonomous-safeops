const isDevVite = typeof window !== "undefined" && window.location.port === "5173";
const API_BASE = isDevVite ? "http://localhost:8000/api" : "/api";

export function getWebSocketUrl() {
  if (typeof window === "undefined") return "ws://localhost:8000/ws/events";
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = isDevVite ? "localhost:8000" : window.location.host;
  return `${protocol}//${host}/ws/events`;
}

export async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });
  if (!res.ok) {
    let errMessage = `HTTP error ${res.status}`;
    try {
      const err = await res.json();
      errMessage = err.detail || errMessage;
    } catch (_) {}
    throw new Error(errMessage);
  }
  return res.json();
}

// Incidents
export const getIncidents = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return fetchJson(`/incidents${query ? `?${query}` : ""}`);
};
export const getIncidentDetail = (id) => fetchJson(`/incidents/${id}`);
export const triggerManualRollback = (id, reason) =>
  fetchJson(`/incidents/${id}/rollback`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });

// Approvals
export const getApprovals = (status) =>
  fetchJson(`/approvals${status ? `?status=${status}` : ""}`);
export const decideApproval = (id, decision, approver, rationale) =>
  fetchJson(`/approvals/${id}/decide`, {
    method: "POST",
    body: JSON.stringify({ decision, approver, rationale }),
  });

// Safety
export const getSafetyStatus = () => fetchJson("/safety");
export const toggleKillSwitch = (active, reason) =>
  fetchJson("/safety/kill-switch", {
    method: "POST",
    body: JSON.stringify({ active, reason }),
  });
export const togglePauseService = (service, paused) =>
  fetchJson("/safety/pause-service", {
    method: "POST",
    body: JSON.stringify({ service, paused }),
  });

// Simulator
export const getInfraTelemetry = () => fetchJson("/simulator/infra");
export const resetInfra = () => fetchJson("/simulator/reset", { method: "POST" });
export const injectFault = (fault_type, host = "host-01", service = null, custom_params = null) =>
  fetchJson("/simulator/inject", {
    method: "POST",
    body: JSON.stringify({ fault_type, host, service, custom_params }),
  });
export const runDemoScenario = () =>
  fetchJson("/simulator/run-demo-scenario", { method: "POST" });

// Runbooks & Policy
export const getRunbooks = () => fetchJson("/runbooks");
export const getRunbookDetail = (id) => fetchJson(`/runbooks/${id}`);
export const getPolicyData = () => fetchJson("/runbooks/policy/all");

// Audit & Changes
export const getAuditEvents = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return fetchJson(`/audit${query ? `?${query}` : ""}`);
};
export const verifyAuditChain = () => fetchJson("/audit/verify");
export const getChangeRecords = (params = {}) => {
  const query = new URLSearchParams(params).toString();
  return fetchJson(`/audit/changes${query ? `?${query}` : ""}`);
};
export const getExportJsonUrl = () => `${API_BASE}/audit/export/json`;
export const getExportCsvUrl = () => `${API_BASE}/audit/export/csv`;

// Metrics
export const getMetrics = () => fetchJson("/metrics");

// Backend Tests Execution API
export const runBackendTests = () => fetchJson("/tests/run", { method: "POST" });
