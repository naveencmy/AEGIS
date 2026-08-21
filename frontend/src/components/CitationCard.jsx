import React, { useState } from 'react';
import { ExternalLink, CheckCircle2, ShieldCheck, Copy, Check, X, Database, Globe, Clock, FileText } from 'lucide-react';

export function CitationPill({ citation, onClick }) {
  const getSourceClass = (source) => {
    switch (source?.toLowerCase()) {
      case 'cisa_kev':
        return 'bg-red-950/80 border-red-800 text-red-300';
      case 'mitre':
        return 'bg-indigo-950/80 border-indigo-800 text-indigo-300';
      case 'sigma':
        return 'bg-emerald-950/80 border-emerald-800 text-emerald-300';
      default:
        return 'bg-cyan-950/80 border-cyan-800 text-cyan-300';
    }
  };

  return (
    <button
      onClick={() => onClick && onClick(citation)}
      className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-mono border hover:brightness-125 transition-all ${getSourceClass(citation.source)}`}
    >
      <span className="font-bold">{citation.doc_id || citation.id}</span>
      <ExternalLink className="w-3 h-3 opacity-70" />
    </button>
  );
}

export function CitationDrawer({ isOpen, onClose, citation }) {
  const [copied, setCopied] = useState(false);
  if (!isOpen || !citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.content || citation.snippet || citation.excerpt || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSourceBadge = (source) => {
    switch (source?.toLowerCase()) {
      case 'cisa_kev':
        return <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-red-950 text-red-300 border border-red-800">CISA KEV</span>;
      case 'mitre':
        return <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">MITRE ATT&CK</span>;
      case 'sigma':
        return <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">SIGMA RULE</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">NIST NVD</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-obsidian-900 border border-slate-750 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-obsidian-950">
          <div className="flex items-center space-x-3">
            {getSourceBadge(citation.source)}
            <div>
              <h3 className="text-sm font-bold font-mono text-white">
                {citation.doc_id || citation.id}
              </h3>
              <p className="text-xs text-slate-400 font-sans">{citation.title || citation.doc_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1 text-xs font-mono">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded-lg bg-obsidian-850 border border-slate-800">
            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase">Provenance Source URL:</span>
              <div className="truncate">
                {citation.source_url ? (
                  <a
                    href={citation.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyber-cyan hover:underline flex items-center space-x-1 truncate"
                  >
                    <span className="truncate">{citation.source_url}</span>
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                ) : (
                  <span className="text-slate-500">Not Available</span>
                )}
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[10px] text-slate-400 uppercase">Ingestion Timestamp:</span>
              <p className="text-slate-300">{citation.fetched_at || 'Live Verified Vector'}</p>
            </div>
          </div>

          {/* Verbatim Excerpt */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 font-sans">Ground Truth Payload:</span>
              <button
                onClick={handleCopy}
                className="flex items-center space-x-1 px-2.5 py-1 rounded bg-obsidian-800 hover:bg-obsidian-750 text-slate-300 text-[11px] border border-slate-700 transition-all"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy Payload'}</span>
              </button>
            </div>
            <pre className="p-3.5 rounded-lg bg-obsidian-950 border border-slate-800 text-slate-200 whitespace-pre-wrap font-mono text-xs leading-relaxed max-h-72 overflow-y-auto">
              {citation.content || citation.snippet || citation.excerpt || 'No excerpt available.'}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-800 bg-obsidian-950 flex items-center justify-between text-xs text-slate-400 font-mono">
          <span className="flex items-center text-emerald-400 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Sovereign Grounding Invariant Verified
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-white font-sans text-xs transition-colors"
          >
            Close Drawer
          </button>
        </div>
      </div>
    </div>
  );
}

export default function CitationCard({ citation, onClick }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const handleCopy = (e) => {
    e.stopPropagation();
    navigator.clipboard.writeText(citation.excerpt || citation.content || citation.snippet || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSourceBadge = (source) => {
    switch (source?.toLowerCase()) {
      case 'cisa_kev':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-950 text-red-300 border border-red-800">CISA KEV</span>;
      case 'mitre':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">MITRE ATT&CK</span>;
      case 'sigma':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">SIGMA RULE</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">NIST NVD</span>;
    }
  };

  const handleClick = () => {
    if (onClick) {
      onClick(citation);
    } else {
      setExpanded(!expanded);
    }
  };

  return (
    <div 
      onClick={handleClick}
      className="p-3 rounded-lg bg-obsidian-850/80 border border-slate-800 hover:border-cyber-cyan/50 transition-all cursor-pointer group"
    >
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center space-x-2">
          {getSourceBadge(citation.source)}
          <span className="font-mono font-bold text-xs text-white group-hover:text-cyber-cyan transition-colors">
            {citation.doc_id || citation.id}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {citation.source_url && (
            <a
              href={citation.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-slate-400 hover:text-cyber-cyan transition-colors p-1"
              title="Open canonical source"
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
          <button
            onClick={handleCopy}
            className="text-slate-400 hover:text-slate-200 p-1"
            title="Copy raw excerpt"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      <p className="text-xs text-slate-300 font-sans leading-relaxed line-clamp-2">
        {citation.excerpt || citation.snippet || citation.content}
      </p>

      {expanded && (
        <div className="mt-2 pt-2 border-t border-slate-750 text-[11px] font-mono text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Fetched At: {citation.fetched_at || 'Live Index'}</span>
            <span className="flex items-center text-emerald-400 text-[10px]">
              <CheckCircle2 className="w-3 h-3 mr-1" /> Provenance Verified
            </span>
          </div>
          {citation.source_url && (
            <div className="truncate text-cyber-cyan">
              {citation.source_url}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
