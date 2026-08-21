import React, { useState, useEffect } from 'react';
import { Shield, Terminal, Compass, Zap, Activity, Server } from 'lucide-react';
import StatsBar from './components/StatsBar';
import ChatPanel from './components/ChatPanel';
import ScanUpload from './components/ScanUpload';
import ThreatExplorer from './components/ThreatExplorer';
import IngestionPanel from './components/IngestionPanel';
import SystemDiagnostics from './components/SystemDiagnostics';
import { getStats, getHealth } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);

  const fetchTelemetry = async () => {
    try {
      const s = await getStats();
      setStats(s);
    } catch (err) {
      console.warn('Stats fetch error:', err.message);
    }
    try {
      const h = await getHealth();
      setHealth(h);
    } catch (err) {
      console.warn('Health fetch error:', err.message);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 60000);
    return () => clearInterval(interval);
  }, []);

  const isKbEmpty = stats ? stats.total_documents === 0 : false;

  return (
    <div className="min-h-screen bg-obsidian-950 text-slate-100 flex flex-col font-sans cyber-grid selection:bg-cyber-indigo/40 selection:text-cyber-cyan">
      {/* Top Sovereign Stats Bar */}
      <StatsBar stats={stats} health={health} />

      {/* Main Header & Nav */}
      <header className="border-b border-slate-800 bg-obsidian-900/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('chat')}>
            <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-indigo/30 via-obsidian-850 to-cyber-cyan/30 border border-cyber-cyan/40 glow-cyan">
              <Shield className="w-6 h-6 text-cyber-cyan" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-black tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-cyber-cyan">
                  AEGIS
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-cyber-indigo/20 border border-cyber-indigo/40 text-cyber-indigo-glow font-mono font-bold">
                  MVP v0.1
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono tracking-tight">
                Sovereign Citation-Native Cybersecurity Co-Pilot
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 bg-obsidian-950 p-1 rounded-lg border border-slate-800">
            <button
              id="tab-chat"
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'chat'
                  ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-850'
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>Co-Pilot Chat</span>
            </button>

            <button
              id="tab-scan"
              onClick={() => setActiveTab('scan')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'scan'
                  ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-850'
              }`}
            >
              <Server className="w-4 h-4" />
              <span>Nmap Scan Analysis</span>
            </button>

            <button
              id="tab-explorer"
              onClick={() => setActiveTab('explorer')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'explorer'
                  ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-850'
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>Threat Explorer</span>
            </button>

            <button
              id="tab-ingestion"
              onClick={() => setActiveTab('ingestion')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'ingestion'
                  ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-850'
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Live Ingestion</span>
            </button>

            <button
              id="tab-diagnostics"
              onClick={() => setActiveTab('diagnostics')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'diagnostics'
                  ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-850'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Guard & System</span>
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6">
        {activeTab === 'chat' && <ChatPanel isKbEmpty={isKbEmpty} />}
        {activeTab === 'scan' && <ScanUpload />}
        {activeTab === 'explorer' && <ThreatExplorer />}
        {activeTab === 'ingestion' && <IngestionPanel onSyncCompleted={fetchTelemetry} />}
        {activeTab === 'diagnostics' && <SystemDiagnostics health={health} kbStats={stats} />}
      </main>

      {/* Sovereign Footer */}
      <footer className="border-t border-slate-800 bg-obsidian-950 py-3 text-center text-xs font-mono text-slate-500 flex items-center justify-between px-6">
        <span>AEGIS SENTINEL v0.1.0 • Sovereign Air-Gapped Cyber Intelligence</span>
        <div className="flex items-center space-x-4">
          <span className="text-emerald-400">✓ Hallucination Guard: Active</span>
          <span className="text-slate-400">Deterministic Seed: 42</span>
        </div>
      </footer>
    </div>
  );
}
