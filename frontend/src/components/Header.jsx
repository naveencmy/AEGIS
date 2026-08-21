import React from 'react';
import { Shield, ShieldAlert, Database, Cpu, Activity, Lock, Terminal, Compass, Zap } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, kbStats, health }) {
  const totalDocs = kbStats?.total_documents || 0;

  return (
    <header className="border-b border-slate-800 bg-obsidian-950/80 backdrop-blur-md sticky top-0 z-40">
      {/* Top Sovereign Status Bar */}
      <div className="border-b border-slate-850 bg-obsidian-950 px-4 py-1.5 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5 text-cyber-cyan font-semibold">
            <Lock className="w-3.5 h-3.5 text-cyber-cyan" />
            <span>SOVEREIGN AIR-GAPPED DEPLOYMENT</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1.5 text-slate-400">
            <Cpu className="w-3.5 h-3.5 text-cyber-indigo" />
            <span>MODEL: Mistral-7B-Instruct-v0.3 (Q4 Local)</span>
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span>DETERMINISM: Seed=42, Temp=0.1, Top-P=0.9</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/60 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>GUARD: ACTIVE</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-obsidian-800 border border-slate-700 text-slate-300">
            <Database className="w-3 h-3 text-cyber-cyan" />
            <span className="font-bold text-cyber-cyan">{totalDocs}</span>
            <span>VERIFIED RECORDS</span>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Brand Logo */}
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

        {/* Tab Buttons */}
        <nav className="flex items-center space-x-1 bg-obsidian-900/90 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'chat'
                ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-800'
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Co-Pilot Reasoning</span>
          </button>

          <button
            onClick={() => setActiveTab('explorer')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'explorer'
                ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-800'
            }`}
          >
            <Compass className="w-4 h-4" />
            <span>Threat Explorer</span>
          </button>

          <button
            onClick={() => setActiveTab('ingestion')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'ingestion'
                ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-800'
            }`}
          >
            <Zap className="w-4 h-4" />
            <span>Live Ingestion</span>
          </button>

          <button
            onClick={() => setActiveTab('diagnostics')}
            className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'diagnostics'
                ? 'bg-cyber-indigo text-white shadow-md shadow-cyber-indigo/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-800'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Guard & System</span>
          </button>
        </nav>
      </div>
    </header>
  );
}
