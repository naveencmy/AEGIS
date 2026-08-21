import React from 'react';
import { AlertTriangle, AlertCircle, Shield, Info } from 'lucide-react';

export default function SeverityBadge({ score, severity }) {
  const sev = (severity || (score >= 9.0 ? 'CRITICAL' : score >= 7.0 ? 'HIGH' : score >= 4.0 ? 'MEDIUM' : score > 0 ? 'LOW' : 'UNKNOWN')).toUpperCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';
  let Icon = Info;

  if (sev === 'CRITICAL') {
    colorClasses = 'bg-red-950/70 text-red-400 border-red-800/80 glow-red';
    Icon = AlertCircle;
  } else if (sev === 'HIGH') {
    colorClasses = 'bg-orange-950/70 text-orange-400 border-orange-800/80 glow-amber';
    Icon = AlertTriangle;
  } else if (sev === 'MEDIUM') {
    colorClasses = 'bg-amber-950/70 text-amber-300 border-amber-800/80';
    Icon = AlertTriangle;
  } else if (sev === 'LOW') {
    colorClasses = 'bg-emerald-950/70 text-emerald-400 border-emerald-800/80';
    Icon = Shield;
  }

  return (
    <span className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${colorClasses}`}>
      <Icon className="w-3 h-3" />
      <span>{sev}</span>
      {score !== undefined && score !== null && <span>({score})</span>}
    </span>
  );
}
