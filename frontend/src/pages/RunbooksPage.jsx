import React, { useState, useEffect } from "react";
import {
  FileCode,
  Shield,
  Layers,
  Key,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Lock,
  ChevronRight
} from "lucide-react";
import { getRunbooks, getRunbookDetail, getPolicyData } from "../api";

export default function RunbooksPage() {
  const [activeTab, setActiveTab] = useState("runbooks"); // "runbooks" or "policy"
  const [runbooks, setRunbooks] = useState([]);
  const [selectedRunbookId, setSelectedRunbookId] = useState(null);
  const [runbookDetail, setRunbookDetail] = useState(null);
  const [policyData, setPolicyData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getRunbooks(), getPolicyData()])
      .then(([rbList, pol]) => {
        setRunbooks(rbList);
        setPolicyData(pol);
        if (rbList.length > 0) {
          setSelectedRunbookId(rbList[0].id);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!selectedRunbookId) return;
    getRunbookDetail(selectedRunbookId)
      .then((res) => setRunbookDetail(res))
      .catch((err) => console.error(err));
  }, [selectedRunbookId]);

  return (
    <div className="space-y-6">

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-800">
        <button
          onClick={() => setActiveTab("runbooks")}
          className={`pb-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "runbooks"
              ? "border-cyan-400 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <FileCode className="h-4 w-4" />
          <span>Runbooks as Code ({runbooks.length})</span>
        </button>
        <button
          onClick={() => setActiveTab("policy")}
          className={`pb-3 text-sm font-bold border-b-2 transition-all flex items-center gap-2 ${
            activeTab === "policy"
              ? "border-cyan-400 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Shield className="h-4 w-4" />
          <span>Global Safety Policy (policy.yaml)</span>
        </button>
      </div>

      {loading ? (
        <div className="p-16 text-center text-slate-400">Loading runbooks and policy rules...</div>
      ) : activeTab === "runbooks" ? (
        
        /* RUNBOOKS TAB */
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Runbook Sidebar */}
          <div className="md:col-span-4 space-y-2">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Registered Safe Runbooks
            </div>
            <div className="space-y-1.5 max-h-[75vh] overflow-y-auto pr-1">
              {runbooks.map((rb) => {
                const isSelected = selectedRunbookId === rb.id;
                return (
                  <button
                    key={rb.id}
                    onClick={() => setSelectedRunbookId(rb.id)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      isSelected
                        ? "border-cyan-500/50 bg-cyan-950/20 text-white"
                        : "border-slate-800/80 bg-night-900 text-slate-400 hover:border-slate-700 hover:text-slate-200"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono text-[11px] font-bold text-cyan-400">{rb.id}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rb.risk_tier === 0
                          ? "bg-emerald-500/10 text-emerald-400"
                          : rb.risk_tier === 1
                          ? "bg-cyan-500/10 text-cyan-400"
                          : "bg-amber-500/10 text-amber-400"
                      }`}>
                        Tier {rb.risk_tier}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-slate-200 truncate">
                      {rb.name}
                    </div>
                    <div className="text-[11px] text-slate-500 truncate mt-0.5">
                      Scope: {rb.required_credential_scope}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Runbook Details & YAML Viewer */}
          <div className="md:col-span-8">
            {runbookDetail ? (
              <div className="rounded-2xl border border-slate-800 bg-night-900 p-6 space-y-5">
                
                {/* Header */}
                <div className="border-b border-slate-800 pb-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-cyan-400 bg-night-950 px-2.5 py-1 rounded border border-slate-800">
                      {runbookDetail.metadata?.id}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      Tier {runbookDetail.metadata?.risk_tier} Risk
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mt-2">
                    {runbookDetail.metadata?.name}
                  </h3>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                    {runbookDetail.metadata?.description}
                  </p>
                </div>

                {/* Scope & Blast Radius Tags */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                  <div className="rounded-xl border border-slate-800 bg-night-850 p-3">
                    <span className="text-[11px] text-slate-500 block uppercase tracking-wider mb-1">Required Scope</span>
                    <span className="font-mono font-bold text-amber-400 flex items-center gap-1">
                      <Key className="h-3.5 w-3.5" /> {runbookDetail.metadata?.required_credential_scope}
                    </span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-night-850 p-3">
                    <span className="text-[11px] text-slate-500 block uppercase tracking-wider mb-1">Max Hosts</span>
                    <span className="font-mono font-bold text-white">
                      {runbookDetail.metadata?.blast_radius?.max_hosts || 1} Host Bound
                    </span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-night-850 p-3">
                    <span className="text-[11px] text-slate-500 block uppercase tracking-wider mb-1">Service Scope</span>
                    <span className="font-mono font-bold text-purple-400">
                      {runbookDetail.metadata?.blast_radius?.service_scope || "Local"}
                    </span>
                  </div>
                </div>

                {/* Steps and Rollback Steps */}
                <div className="space-y-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Execution Steps ({runbookDetail.metadata?.action_steps?.length || 0})
                  </div>
                  <div className="space-y-2">
                    {runbookDetail.metadata?.action_steps?.map((step) => (
                      <div key={step.step} className="rounded-xl border border-slate-800/80 bg-night-850 p-3 text-xs flex items-start gap-3">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 font-mono font-bold text-[11px]">
                          {step.step}
                        </span>
                        <div>
                          <div className="font-bold text-slate-200">{step.name}</div>
                          <div className="font-mono text-[11px] text-slate-500 mt-0.5">
                            Action: <strong className="text-slate-400">{step.action}</strong> &bull; Target: <strong className="text-slate-400">{step.target}</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="text-xs font-bold uppercase tracking-wider text-amber-400 pt-2 flex items-center gap-1.5">
                    <RotateCcw className="h-3.5 w-3.5" /> Rollback Contract Steps ({runbookDetail.metadata?.rollback_steps?.length || 0})
                  </div>
                  <div className="space-y-2">
                    {runbookDetail.metadata?.rollback_steps?.map((step) => (
                      <div key={step.step} className="rounded-xl border border-amber-500/20 bg-amber-950/10 p-3 text-xs flex items-start gap-3">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-500/10 text-amber-400 font-mono font-bold text-[11px]">
                          {step.step}
                        </span>
                        <div>
                          <div className="font-bold text-amber-200">{step.name}</div>
                          <div className="font-mono text-[11px] text-amber-400/80 mt-0.5">
                            Restore: <strong className="text-amber-300">{step.action}</strong> &bull; Target: {step.target}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Raw YAML */}
                <div>
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Source Runbook YAML Definition
                  </div>
                  <pre className="p-4 rounded-xl bg-night-950 text-xs font-mono text-cyan-300 overflow-x-auto border border-slate-800">
                    {runbookDetail.raw_yaml}
                  </pre>
                </div>

              </div>
            ) : null}
          </div>
        </div>
      ) : (

        /* POLICY TAB */
        <div className="rounded-2xl border border-slate-800 bg-night-900 p-6 space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Shield className="h-5 w-5 text-cyan-400" />
              {policyData?.policy?.name || "Global Safety Policy"}
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              {policyData?.policy?.description}
            </p>
          </div>

          {/* Policy Tiers Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {policyData?.policy?.tiers && Object.entries(policyData.policy.tiers).map(([key, tier]) => (
              <div key={key} className="rounded-xl border border-slate-800 bg-night-850 p-4 space-y-2">
                <span className="font-mono text-xs font-bold uppercase text-cyan-400">
                  {key.replace("_", " ")}
                </span>
                <div className="font-bold text-white text-sm">{tier.name}</div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {tier.description}
                </p>
                <div className="pt-2 text-[11px] text-slate-500 font-mono">
                  {tier.approval_required ? "Human Approval Required" : `Auto-Run (Rate limit: ${tier.rate_limit_per_hour}/hr)`}
                </div>
              </div>
            ))}
          </div>

          {/* Blast Radius & Protected Surfaces */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-slate-800 bg-night-850 p-4 space-y-2 text-xs">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <Shield className="h-4 w-4 text-cyan-400" /> Blast-Radius Hard Limits
              </span>
              <ul className="space-y-1.5 text-slate-400 font-mono text-[11px]">
                <li>&bull; Max hosts affected simultaneously: <strong className="text-white">2</strong></li>
                <li>&bull; Max executions per service per hour: <strong className="text-white">5</strong></li>
                <li>&bull; Cooldown between actions: <strong className="text-white">15 seconds</strong></li>
              </ul>
            </div>

            <div className="rounded-xl border border-red-500/30 bg-red-950/10 p-4 space-y-2 text-xs">
              <span className="font-bold text-red-300 flex items-center gap-1.5">
                <Lock className="h-4 w-4 text-red-400" /> Tier 3 Strictly Protected Surfaces (Never Touch)
              </span>
              <ul className="space-y-1.5 text-red-400 font-mono text-[11px]">
                <li>&bull; Protected paths: /etc, /boot, /data/core (crash dumps)</li>
                <li>&bull; Protected services: prod-db-primary, auth-hsm, vault-cluster</li>
                <li>&bull; Rule: Strict DENY / ESCALATE on any attempted mutation</li>
              </ul>
            </div>
          </div>

          {/* Raw Policy YAML */}
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Source policy.yaml Content
            </div>
            <pre className="p-4 rounded-xl bg-night-950 text-xs font-mono text-cyan-300 overflow-x-auto border border-slate-800">
              {policyData?.raw_yaml}
            </pre>
          </div>
        </div>
      )}

    </div>
  );
}
