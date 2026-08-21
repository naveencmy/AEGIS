import React from 'react';
import { Database, ShieldCheck, Cpu, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function StatsBar({ stats, health }) {
  const total = stats?.total_documents || 0;
  const nvd = stats?.nvd_cves_count || 0;
  const mitre = stats?.mitre_techniques_count || 0;
  const kev = stats?.cisa_kev_count || 0;
  const sigma = stats?.sigma_rules_count || 0;
  const model = stats?.llm_backend || "Local Mistral (7B-Instruct Q4)";
  const lastIngest = stats?.last_ingest_time ? new Date(stats.last_ingest_time).toLocaleTimeString() : 'Active';

  if (total === 0 && stats !== null) {
    return (
      <div className="bg-amber-950/90 border-b border-amber-600 text-amber-300 px-4 py-2 text-xs font-mono flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-2 font-bold">
          <AlertTriangle className="w-4 h-4 text-amber-400 animate-bounce" />
          <span>Knowledge base empty — run ingestion</span>
        </div>
        <span className="text-[11px] text-amber-200">Chat & Scan correlation disabled until threat intelligence is ingested.</span>
      </div>
    );
  }

  return (
    <div className="bg-obsidian-950 border-b border-slate-800 text-xs font-mono px-4 py-2 flex flex-wrap items-center justify-between gap-2">
      {/* Left: Sovereign Status */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5 text-cyber-cyan font-bold">
          <ShieldCheck className="w-4 h-4 text-cyber-cyan" />
          <span>SOVEREIGN AIR-GAP</span>
        </div>
        <span className="text-slate-700">|</span>
        <div className="flex items-center space-x-1 text-slate-400">
          <Cpu className="w-3.5 h-3.5 text-cyber-indigo" />
          <span>{model}</span>
        </div>
        <span className="text-slate-700 hidden md:inline">|</span>
        <div className="hidden md:flex items-center space-x-1 text-slate-400">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>Synced: {lastIngest}</span>
        </div>
      </div>

      {/* Right: Ingestion Breakdown Counts */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1 bg-obsidian-850 px-2.5 py-0.5 rounded border border-slate-750 text-slate-300">
          <Database className="w-3 h-3 text-cyber-cyan" />
          <span className="font-bold text-cyber-cyan">{total.toLocaleString()}</span>
          <span className="text-[11px] text-slate-400">TOTAL VERIFIED</span>
        </div>
        <div className="hidden sm:flex items-center space-x-2 text-slate-400 text-[11px]">
          <span className="text-amber-400 font-semibold">{kev} KEV</span>
          <span>•</span>
          <span className="text-indigo-400 font-semibold">{mitre} ATT&CK</span>
          <span>•</span>
          <span className="text-emerald-400 font-semibold">{sigma} Sigma</span>
          <span>•</span>
          <span className="text-cyan-400 font-semibold">{nvd} NVD</span>
        </div>
        <div className="flex items-center space-x-1 text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>GUARD ACTIVE</span>
        </div>
      </div>
    </div>
  );
}
