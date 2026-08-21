import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, ShieldCheck, AlertTriangle, RefreshCw, ExternalLink, 
  Copy, Check, FileText, ArrowRight, Zap, Database
} from 'lucide-react';
import { sendChatQuery } from '../api';
import CitationCard, { CitationDrawer } from './CitationCard';
import SeverityBadge from './SeverityBadge';

export default function ChatPanel({ isKbEmpty = false }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterSource, setFilterSource] = useState('all');
  const [selectedCitation, setSelectedCitation] = useState(null);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (customQuery = null) => {
    const q = (customQuery || query).trim();
    if (!q || loading || isKbEmpty) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!customQuery) setQuery('');
    setLoading(true);

    try {
      const filter = filterSource === 'all' ? null : [filterSource];
      const data = await sendChatQuery(q, filter, 0.35);

      const botMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        data: data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'bot',
        error: `Intelligence Engine Error: ${err.response?.data?.detail || err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const renderFormattedAnswer = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return (
      <div className="space-y-2 text-xs font-sans leading-relaxed text-slate-200">
        {lines.map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) return <div key={idx} className="h-1" />;

          if (trimmed.startsWith('### ')) {
            return (
              <h3 key={idx} className="text-sm font-bold font-mono text-cyber-cyan border-b border-slate-800 pb-1 mt-3">
                {trimmed.replace('### ', '')}
              </h3>
            );
          }

          if (trimmed.startsWith('**') && trimmed.endsWith('**:')) {
            return (
              <h4 key={idx} className="font-bold text-cyber-indigo-glow font-mono mt-2 text-xs">
                {trimmed}
              </h4>
            );
          }

          if (trimmed.startsWith('- ')) {
            return (
              <div key={idx} className="flex items-start space-x-2 pl-2">
                <span className="text-cyber-cyan font-bold">•</span>
                <span className="flex-1">{trimmed.replace('- ', '')}</span>
              </div>
            );
          }

          return <p key={idx}>{trimmed}</p>;
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col space-y-4 max-w-5xl mx-auto">
      {/* Citation Deep-Dive Drawer Modal */}
      {selectedCitation && (
        <CitationDrawer
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}

      {/* Header & Quick Prompts */}
      <div className="p-4 rounded-xl bg-obsidian-900 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-cyber-cyan" />
            <h2 className="text-sm font-black tracking-wider text-white font-mono uppercase">
              Sovereign Threat Intelligence Co-Pilot
            </h2>
          </div>
          <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-400">
            <span className="text-emerald-400">✓ Strict JSON Contract</span>
            <span>•</span>
            <span className="text-cyber-cyan">✓ Verified Citations</span>
          </div>
        </div>

        {/* Quick Judge Benchmarks */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-mono text-slate-500">Benchmark Queries:</span>
          <button
            onClick={() => handleSend("Is CVE-2024-21626 critical?")}
            disabled={loading || isKbEmpty}
            className="px-2.5 py-1 rounded bg-obsidian-850 hover:bg-obsidian-800 border border-slate-750 text-cyber-cyan text-xs font-mono transition-all disabled:opacity-50"
          >
            "Is CVE-2024-21626 critical?"
          </button>
          <button
            onClick={() => handleSend("Tell me about CVE-2099-99999")}
            disabled={loading || isKbEmpty}
            className="px-2.5 py-1 rounded bg-obsidian-850 hover:bg-obsidian-800 border border-slate-750 text-amber-300 text-xs font-mono transition-all disabled:opacity-50"
          >
            "Tell me about CVE-2099-99999" (Silence Test)
          </button>
          <button
            onClick={() => handleSend("container escape to host kubernetes")}
            disabled={loading || isKbEmpty}
            className="px-2.5 py-1 rounded bg-obsidian-850 hover:bg-obsidian-800 border border-slate-750 text-indigo-300 text-xs font-mono transition-all disabled:opacity-50"
          >
            "container escape to host kubernetes"
          </button>
        </div>
      </div>

      {/* Message Feed */}
      <div className="space-y-4 min-h-[420px] pb-4">
        {messages.length === 0 && (
          <div className="p-8 rounded-xl bg-obsidian-900/60 border border-slate-800 text-center space-y-3">
            <Database className="w-8 h-8 text-cyber-cyan mx-auto opacity-70" />
            <h3 className="text-sm font-bold text-white font-mono">Sovereign Citation-Native Intelligence Active</h3>
            <p className="text-xs text-slate-400 max-w-lg mx-auto font-sans leading-relaxed">
              Ask about any ingested CVEs, ATT&CK techniques (T1611), CISA KEV active exploits, or Sigma detection logic.
              AEGIS enforces citation-or-silence invariant — every answer is backed by exact document provenance.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className="space-y-2 animate-fadeIn">
            {msg.sender === 'user' ? (
              <div className="flex justify-end">
                <div className="max-w-2xl bg-cyber-indigo/20 border border-cyber-indigo/50 rounded-xl p-3.5 text-xs text-white space-y-1 shadow-lg">
                  <div className="flex items-center justify-between text-[10px] font-mono text-cyber-cyan font-bold">
                    <span>SECURITY ANALYST</span>
                    <span>{msg.timestamp}</span>
                  </div>
                  <p className="leading-relaxed">{msg.text}</p>
                </div>
              </div>
            ) : msg.error ? (
              <div className="p-4 rounded-xl bg-red-950/50 border border-red-800 text-red-300 text-xs flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>{msg.error}</span>
              </div>
            ) : (
              <div className="p-5 rounded-xl bg-obsidian-900 border border-slate-800 space-y-4 shadow-xl">
                {/* Assistant Header & Latency */}
                <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                  <div className="flex items-center space-x-2 font-mono text-xs text-cyber-cyan font-bold">
                    <ShieldCheck className="w-4 h-4 text-cyber-cyan" />
                    <span>AEGIS SENTINEL</span>
                    <span className="text-slate-500 font-normal">({msg.data.latency_ms}ms)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    {msg.data.guard?.unverified_claims_removed && (
                      <span className="px-2.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-mono font-bold animate-pulse">
                        ⚠️ UNVERIFIED CLAIMS STRIPPED BY GUARD
                      </span>
                    )}
                    {msg.data.guard && (
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">
                        {msg.data.guard.ids_verified}/{msg.data.guard.ids_checked} IDs VERIFIED
                      </span>
                    )}
                  </div>
                </div>

                {/* Prominent Amber Silence Banner if Insufficient Evidence */}
                {msg.data.insufficient_evidence ? (
                  <div className="p-4 rounded-xl bg-amber-950/40 border-2 border-amber-500/80 text-amber-300 text-xs font-mono space-y-2 shadow-lg shadow-amber-950/30">
                    <div className="flex items-center space-x-2 font-bold text-amber-400 text-sm">
                      <AlertTriangle className="w-5 h-5 text-amber-400 animate-pulse" />
                      <span>NO VERIFIED INTEL — CITATION OR SILENCE ENFORCED</span>
                    </div>
                    <p className="font-sans text-slate-200 text-sm leading-relaxed">
                      {msg.data.answer || "Insufficient verified intelligence in the knowledge base."}
                    </p>
                    <div className="text-[11px] text-amber-400/80 border-t border-amber-800/50 pt-2 flex items-center justify-between">
                      <span>Invariant 4: Zero ungrounded hallucinations permitted</span>
                      <span className="font-bold text-amber-400">STATUS: REJECTED BY SILENCE GATE</span>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Primary Metadata Badges (CVSS, MITRE, KEV) */}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      {msg.data.cve_ids?.slice(0, 1).map((cid, cIdx) => (
                        <span key={cIdx} className="px-2.5 py-0.5 rounded bg-obsidian-800 text-white border border-slate-700 font-mono text-xs font-bold">
                          {cid}
                        </span>
                      ))}
                      {msg.data.cvss?.score && (
                        <SeverityBadge score={msg.data.cvss.score} severity={msg.data.cvss.severity} />
                      )}
                      {msg.data.mitre_techniques?.map((t, tIdx) => (
                        <span key={tIdx} className="px-2.5 py-0.5 rounded bg-indigo-950/70 text-indigo-300 border border-indigo-800/80 font-mono text-xs">
                          {t.id}: {t.name}
                        </span>
                      ))}
                      {msg.data.cisa_kev?.listed && (
                        <span className="px-2.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-mono text-xs font-bold">
                          CISA KEV EXPLOITED (Due: {msg.data.cisa_kev.due_date || 'Mandatory Action'})
                        </span>
                      )}
                    </div>

                    {/* Prose Answer with Clean Markdown Layout */}
                    {renderFormattedAnswer(msg.data.answer)}

                    {/* Citations Grid — Visual Hero of Each Answer */}
                    {msg.data.citations?.length > 0 && (
                      <div className="space-y-2 pt-3 border-t border-slate-800">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono font-bold text-cyber-cyan uppercase tracking-wider flex items-center space-x-1.5">
                            <ShieldCheck className="w-3.5 h-3.5 text-cyber-cyan" />
                            <span>Verified Provenance Citations ({msg.data.citations.length})</span>
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">Click card to open full citation drawer</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                          {msg.data.citations.map((c, cIdx) => (
                            <CitationCard 
                              key={cIdx} 
                              citation={c} 
                              onClick={(cit) => setSelectedCitation(cit)}
                            />
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="p-4 rounded-xl bg-obsidian-900 border border-slate-800 flex items-center space-x-3 text-xs font-mono text-cyber-cyan animate-pulse">
            <RefreshCw className="w-4 h-4 animate-spin text-cyber-cyan" />
            <span>Retrieving ChromaDB vectors & synthesizing verified citation payload...</span>
          </div>
        )}
        <div ref={chatBottomRef} />
      </div>

      {/* Input Box */}
      <div className="p-3 rounded-xl bg-obsidian-900 border border-slate-800 space-y-2 sticky bottom-4 shadow-2xl backdrop-blur-md">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
          <div className="flex items-center space-x-2">
            <span>Filter Feed:</span>
            <select
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="bg-obsidian-800 border border-slate-700 text-slate-300 rounded px-2 py-0.5 text-xs focus:outline-none focus:border-cyber-cyan"
            >
              <option value="all">All Sources (NVD, MITRE, KEV, Sigma)</option>
              <option value="nvd">NIST NVD Only</option>
              <option value="cisa_kev">CISA KEV Only</option>
              <option value="mitre">MITRE ATT&CK Only</option>
              <option value="sigma">Sigma Rules Only</option>
            </select>
          </div>
          <button
            onClick={() => setMessages([])}
            className="text-slate-500 hover:text-slate-300 text-[11px]"
          >
            Clear Feed
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={query}
            disabled={isKbEmpty || loading}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={isKbEmpty ? "Knowledge base empty — run ingestion first" : "Ask AEGIS co-pilot (e.g. 'Is CVE-2024-21626 critical?' or 'T1611 detection logic')..."}
            className="flex-1 bg-obsidian-950 border border-slate-750 focus:border-cyber-cyan rounded-lg px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none font-sans disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading || isKbEmpty}
            className={`px-5 py-2.5 rounded-lg text-xs font-bold font-mono flex items-center space-x-1.5 transition-all ${
              !query.trim() || loading || isKbEmpty
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-cyber-indigo hover:bg-cyber-indigo-glow text-white shadow-lg shadow-cyber-indigo/30'
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            <span>QUERY</span>
          </button>
        </form>
      </div>
    </div>
  );
}
