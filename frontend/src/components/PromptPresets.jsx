import React from 'react';
import { Sparkles, Shield, AlertOctagon, Terminal, Flame } from 'lucide-react';

const presets = [
  {
    id: 'log4shell',
    title: 'Log4Shell CVE-2021-44228',
    category: 'Vulnerability Analysis',
    icon: Flame,
    color: 'from-amber-500/20 to-rose-500/20 border-amber-600/40 text-amber-300',
    query: 'Analyze Apache Log4j2 CVE-2021-44228: CVSS severity, CISA KEV ransomware exploitation, and mandatory remediation.',
  },
  {
    id: 'mitre_powershell',
    title: 'MITRE T1059.001 PowerShell',
    category: 'ATT&CK Mapping',
    icon: Terminal,
    color: 'from-purple-500/20 to-indigo-500/20 border-purple-600/40 text-purple-300',
    query: 'What are the tactics, platforms, and detection guidance for MITRE ATT&CK technique T1059.001 (Command and Scripting Interpreter: PowerShell)?',
  },
  {
    id: 'sigma_detection',
    title: 'Sigma Detection Engineering',
    category: 'Rule Correlation',
    icon: Shield,
    color: 'from-emerald-500/20 to-teal-500/20 border-emerald-600/40 text-emerald-300',
    query: 'Provide Sigma detection rules, log source criteria, and detection logic for suspicious script and command execution.',
  },
  {
    id: 'silence_test',
    title: 'Invariant 4: Silence on Unindexed Topics',
    category: 'Strict Gating Test',
    icon: AlertOctagon,
    color: 'from-blue-500/20 to-slate-500/20 border-blue-600/40 text-blue-300',
    query: 'Explain the zero-day exploit mechanism for the quantum protocol vulnerability in CVE-2099-99999.',
  },
];

export default function PromptPresets({ onSelectPreset }) {
  return (
    <div className="mb-6">
      <div className="flex items-center space-x-2 text-xs font-mono text-slate-400 mb-2.5">
        <Sparkles className="w-3.5 h-3.5 text-cyber-cyan" />
        <span>EVALUATION & BENCHMARK PRESETS (JUDGE DEMO):</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {presets.map((preset) => {
          const Icon = preset.icon;
          return (
            <button
              key={preset.id}
              onClick={() => onSelectPreset(preset.query)}
              className={`text-left p-3 rounded-lg border bg-gradient-to-br transition-all hover:scale-[1.02] hover:shadow-lg glass-card flex flex-col justify-between ${preset.color}`}
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-[10px] font-mono uppercase tracking-wider opacity-70">
                  {preset.category}
                </span>
                <Icon className="w-4 h-4 opacity-80" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white mb-1">{preset.title}</h4>
                <p className="text-[11px] text-slate-300 line-clamp-2 leading-tight">
                  {preset.query}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
