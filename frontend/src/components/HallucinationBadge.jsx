import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

export default function HallucinationBadge({
  unverifiedClaimsRemoved,
  verifiedIds = [],
  hallucinationsDetected = [],
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
      {/* Primary Guard Status */}
      {unverifiedClaimsRemoved ? (
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-rose-950/80 border border-rose-700/80 text-rose-300 animate-pulse">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span className="font-bold">GUARD ALERT: Unverified Claims Stripped</span>
        </div>
      ) : (
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-emerald-950/70 border border-emerald-700/60 text-emerald-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span className="font-bold">GUARD: 100% Grounded Intelligence</span>
        </div>
      )}

      {/* Verified Entities */}
      {verifiedIds.length > 0 && (
        <div className="flex items-center space-x-1 text-slate-400">
          <span className="text-[11px] text-slate-500">VERIFIED IN DB:</span>
          {verifiedIds.map((id) => (
            <span
              key={id}
              className="px-1.5 py-0.5 rounded bg-emerald-950/40 border border-emerald-800 text-emerald-300 font-bold text-[11px]"
            >
              ✓ {id}
            </span>
          ))}
        </div>
      )}

      {/* Intercepted Fake Entities */}
      {hallucinationsDetected.length > 0 && (
        <div className="flex items-center space-x-1 text-rose-400">
          <span className="text-[11px] text-rose-500 font-semibold">INTERCEPTED HALLUCINATIONS:</span>
          {hallucinationsDetected.map((id) => (
            <span
              key={id}
              className="px-1.5 py-0.5 rounded bg-rose-950/60 border border-rose-800 text-rose-300 font-bold text-[11px] line-through"
            >
              ✕ {id}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
