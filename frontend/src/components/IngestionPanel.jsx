import React, { useState, useEffect } from 'react';
import { Zap, Play, RefreshCw, AlertTriangle, CheckCircle, Clock, Shield, Terminal, ArrowRight, Gauge } from 'lucide-react';
import { getIngestionStatus, triggerIngestion, syncSource } from '../services/api';

const sourceInfo = [
  {
    id: 'cisa_kev',
    name: 'CISA KEV Catalog',
    badge: 'CISA KEV',
    color: 'border-rose-700/60 bg-rose-950/40 text-rose-300',
    url: 'https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json',
    desc: 'Live feed of actively exploited zero-days and ransomware vulnerabilities with remediation deadlines.',
    defaultLimit: 50,
  },
  {
    id: 'mitre',
    name: 'MITRE ATT&CK Enterprise',
    badge: 'STIX 2.1',
    color: 'border-purple-700/60 bg-purple-950/40 text-purple-300',
    url: 'https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json',
    desc: 'Adversary tactics, techniques, and procedures (TTPs) across Windows, Linux, Cloud, and macOS.',
    defaultLimit: 50,
  },
  {
    id: 'sigma',
    name: 'SigmaHQ Detection Rules',
    badge: 'YAML Rules',
    color: 'border-emerald-700/60 bg-emerald-950/40 text-emerald-300',
    url: 'https://github.com/SigmaHQ/sigma',
    desc: 'Generic detection signatures mapped to ATT&CK techniques and log sources.',
    defaultLimit: 50,
  },
  {
    id: 'nvd',
    name: 'NVD API 2.0 (NIST)',
    badge: 'Rate Limited (5/30s)',
    color: 'border-indigo-700/60 bg-indigo-950/40 text-indigo-300',
    url: 'https://services.nvd.nist.gov/rest/json/cves/2.0',
    desc: 'Comprehensive National Vulnerability Database CVE records with CVSS scores and CWEs.',
    defaultLimit: 20,
    rateLimited: true,
  },
];

export default function IngestionPanel({ onRefreshStats }) {
  const [statusData, setStatusData] = useState(null);
  const [limits, setLimits] = useState({
    cisa_kev: 50,
    mitre: 50,
    sigma: 50,
    nvd: 20,
  });
  const [syncingSource, setSyncingSource] = useState(null);
  const [logs, setLogs] = useState([
    `[${new Date().toLocaleTimeString()}] AEGIS Sovereign Ingestion Subsystem Standby.`,
    `[${new Date().toLocaleTimeString()}] Ready to pull live threat intelligence without synthetic fallbacks.`,
  ]);

  const addLog = (text) => {
    setLogs((prev) => [...prev.slice(-30), `[${new Date().toLocaleTimeString()}] ${text}`]);
  };

  const fetchStatus = async () => {
    try {
      const data = await getIngestionStatus();
      setStatusData(data);
    } catch (err) {
      console.error('Failed to get ingestion status:', err);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSyncSingle = async (sourceId) => {
    setSyncingSource(sourceId);
    addLog(`Initiating live sync for ${sourceId.toUpperCase()} (Limit: ${limits[sourceId] || 'Full'})...`);
    try {
      const res = await syncSource(sourceId, limits[sourceId], true);
      addLog(`[SUCCESS] ${sourceId.toUpperCase()} sync completed: ${res.records_upserted} records upserted into ChromaDB.`);
      fetchStatus();
      if (onRefreshStats) onRefreshStats();
    } catch (err) {
      addLog(`[ERROR] ${sourceId.toUpperCase()} failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncingSource(null);
    }
  };

  const handleSyncAll = async () => {
    setSyncingSource('all');
    addLog('Launching master multi-source ingestion pipeline...');
    try {
      await triggerIngestion(null, 50, true);
      addLog('Master pipeline launched in background. Monitoring progress...');
    } catch (err) {
      addLog(`[ERROR] Pipeline failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSyncingSource(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Top Banner & Control Bar */}
      <div className="bg-obsidian-850 border border-slate-800 rounded-xl p-5 mb-6 glass-panel flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-cyber-cyan" />
            <h2 className="text-lg font-bold text-white">Live Threat Intelligence Ingestion Controller</h2>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Strict real-data ingestion adhering to Invariants 1 & 6 (Zero synthetic fallbacks, 3-retry backoff, NVD rate throttling).
          </p>
        </div>

        <button
          onClick={handleSyncAll}
          disabled={syncingSource !== null || statusData?.is_running}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyber-indigo to-cyber-cyan hover:from-cyber-indigo-glow hover:to-cyber-cyan-glow text-white font-mono font-bold text-xs transition shadow-lg shadow-cyber-indigo/25 disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          <span>Sync All Live Sources</span>
        </button>
      </div>

      {/* 4 Feeds Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {sourceInfo.map((feed) => {
          const task = statusData?.tasks?.[feed.id];
          const isBusy = syncingSource === feed.id || task?.status === 'running';

          return (
            <div
              key={feed.id}
              className="bg-obsidian-850 border border-slate-800 rounded-xl p-5 flex flex-col justify-between glass-card"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold border ${feed.color}`}>
                      {feed.badge}
                    </span>
                    <h3 className="text-sm font-bold text-white font-mono">{feed.name}</h3>
                  </div>

                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold ${
                      task?.status === 'completed'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : task?.status === 'running'
                        ? 'bg-amber-950 text-amber-400 border border-amber-800 animate-pulse'
                        : task?.status === 'failed'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-slate-900 text-slate-400 border border-slate-800'
                    }`}
                  >
                    {task?.status || 'idle'}
                  </span>
                </div>

                <p className="text-xs text-slate-300 font-sans mb-3 leading-relaxed">
                  {feed.desc}
                </p>

                <div className="text-[11px] font-mono text-slate-500 bg-obsidian-950 p-2.5 rounded-lg border border-slate-850 space-y-1 mb-4">
                  <div className="flex items-center justify-between">
                    <span>ENDPOINT:</span>
                    <span className="text-slate-400 truncate max-w-[240px]">{feed.url}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>INDEXED RECORDS:</span>
                    <span className="text-cyber-cyan font-bold">
                      {statusData?.db_breakdown?.[feed.id] || 0} docs
                    </span>
                  </div>
                  {feed.rateLimited && (
                    <div className="flex items-center justify-between text-amber-400">
                      <span className="flex items-center space-x-1">
                        <Gauge className="w-3 h-3" />
                        <span>RATE THROTTLE:</span>
                      </span>
                      <span>5 req / 30s (6.2s delay)</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
                <div className="flex items-center space-x-2 text-xs font-mono text-slate-400">
                  <span>LIMIT:</span>
                  <input
                    type="number"
                    value={limits[feed.id]}
                    onChange={(e) =>
                      setLimits((prev) => ({
                        ...prev,
                        [feed.id]: parseInt(e.target.value) || 10,
                      }))
                    }
                    className="w-16 bg-obsidian-950 border border-slate-700 rounded px-2 py-1 text-xs text-white font-mono"
                    min="1"
                    max="5000"
                  />
                </div>

                <button
                  onClick={() => handleSyncSingle(feed.id)}
                  disabled={isBusy || statusData?.is_running}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-obsidian-800 hover:bg-obsidian-750 text-cyber-cyan border border-slate-700 text-xs font-mono font-semibold transition disabled:opacity-50"
                >
                  <RefreshCw className={`w-3 h-3 ${isBusy ? 'animate-spin' : ''}`} />
                  <span>{isBusy ? 'Syncing...' : 'Sync Live'}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Terminal Console Logs */}
      <div className="bg-obsidian-950 border border-slate-800 rounded-xl overflow-hidden glass-panel">
        <div className="px-4 py-2.5 bg-obsidian-900 border-b border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
          <div className="flex items-center space-x-2">
            <Terminal className="w-3.5 h-3.5 text-cyber-cyan" />
            <span className="font-bold text-slate-200">LIVE INGESTION & PIPELINE TELEMETRY CONSOLE</span>
          </div>
          <span className="text-[10px] text-slate-500">REAL-TIME EVENT STREAM</span>
        </div>
        <div className="p-4 font-mono text-xs text-slate-300 space-y-1.5 max-h-48 overflow-y-auto bg-obsidian-950/90">
          {logs.map((l, i) => (
            <div key={i} className="flex items-start space-x-2">
              <span className="text-cyber-indigo select-none">&gt;</span>
              <span
                className={
                  l.includes('[ERROR]')
                    ? 'text-rose-400'
                    : l.includes('[SUCCESS]')
                    ? 'text-emerald-400'
                    : 'text-slate-300'
                }
              >
                {l}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
