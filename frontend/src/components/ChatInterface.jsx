import React, { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Shield, AlertOctagon, RotateCcw, Filter, ChevronDown, Clock, Cpu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { queryAEGIS } from '../services/api';
import PromptPresets from './PromptPresets';
import HallucinationBadge from './HallucinationBadge';
import { CitationPill, CitationDrawer } from './CitationCard';

export default function ChatInterface({ kbStats, onRefreshStats }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        '### AEGIS Sovereign Cybersecurity Co-Pilot Initialized.\n\nAll intelligence queries are strictly grounded in local ChromaDB vectors ingested live from **NVD API 2.0**, **MITRE ATT&CK STIX 2.1**, **CISA KEV**, and **SigmaHQ detection rules**.\n\n- **Provenance Invariant**: Every factual claim is backed by cryptographically verifiable document IDs.\n- **Silence Invariant**: If intelligence is missing or below the relevance threshold, AEGIS responds with silence rather than hallucinating.',
      citations: [],
      verified_ids: [],
      hallucinations_detected: [],
      unverified_claims_removed: false,
      silence_triggered: false,
      execution_time_ms: 0,
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSource, setSelectedSource] = useState('all');
  const [activeCitation, setActiveCitation] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (queryText = inputQuery) => {
    const textToSend = queryText.trim();
    if (!textToSend || isLoading) return;

    const userMessage = {
      role: 'user',
      content: textToSend,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const filterSources = selectedSource === 'all' ? null : [selectedSource];
      const result = await queryAEGIS(textToSend, filterSources);

      const assistantMessage = {
        role: 'assistant',
        content: result.answer,
        citations: result.citations || [],
        verified_ids: result.verified_ids || [],
        hallucinations_detected: result.hallucinations_detected || [],
        unverified_claims_removed: result.unverified_claims_removed || false,
        silence_triggered: result.silence_triggered || false,
        retrieval_confidence: result.retrieval_confidence || 0,
        execution_time_ms: result.execution_time_ms || 0,
        model_used: result.model_used || 'Mistral-7B',
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      if (onRefreshStats) onRefreshStats();
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: `**System Communication Error**: Failed to reach AEGIS RAG backend. ${err.response?.data?.detail || err.message}`,
        citations: [],
        silence_triggered: false,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = () => {
    setMessages([messages[0]]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-7xl mx-auto px-4 py-4">
      {/* Evaluation Presets for Judge Demos */}
      <PromptPresets onSelectPreset={(q) => handleSend(q)} />

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 mb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${
              msg.role === 'user' ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-4xl rounded-xl p-4 shadow-md transition-all ${
                msg.role === 'user'
                  ? 'bg-cyber-indigo text-white rounded-br-none ml-12'
                  : 'bg-obsidian-850 border border-slate-800 text-slate-200 rounded-bl-none mr-12 glass-panel'
              }`}
            >
              {/* Header Info */}
              <div className="flex items-center justify-between space-x-4 mb-2 pb-1.5 border-b border-slate-700/50 text-[11px] font-mono text-slate-400">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-cyber-cyan">
                    {msg.role === 'user' ? 'OPERATOR' : 'AEGIS SENTINEL'}
                  </span>
                  {msg.execution_time_ms > 0 && (
                    <span className="text-slate-500 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{Math.round(msg.execution_time_ms)}ms</span>
                    </span>
                  )}
                </div>
                <span>{msg.timestamp}</span>
              </div>

              {/* Silence Alert Banner */}
              {msg.silence_triggered && (
                <div className="mb-3 p-3 rounded-lg bg-blue-950/60 border border-blue-700/60 text-blue-300 text-xs font-mono flex items-start space-x-2">
                  <AlertOctagon className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="font-bold block">INVARIANT 4 ENFORCED (CITATION OR SILENCE):</span>
                    <span>
                      Retrieval confidence below verified threshold ({Math.round((msg.retrieval_confidence || 0) * 100)}%).
                      AEGIS refused speculative generation to prevent false security intelligence.
                    </span>
                  </div>
                </div>
              )}

              {/* Message Content */}
              <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed font-sans">
                <ReactMarkdown
                  components={{
                    p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2" {...props} />,
                    ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2" {...props} />,
                    code: ({ node, inline, ...props }) =>
                      inline ? (
                        <code className="px-1.5 py-0.5 rounded bg-obsidian-950 text-cyber-cyan font-mono text-xs border border-slate-800" {...props} />
                      ) : (
                        <code className="block p-3 rounded-lg bg-obsidian-950 font-mono text-xs text-slate-300 border border-slate-800 my-2 overflow-x-auto" {...props} />
                      ),
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>

              {/* Citations and Provenance Chips */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800/80">
                  <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center space-x-1.5">
                    <Shield className="w-3.5 h-3.5 text-cyber-cyan" />
                    <span>VERIFIED PROVENANCE CITATIONS ({msg.citations.length}):</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((c, cIdx) => (
                      <CitationPill
                        key={cIdx}
                        citation={c}
                        onClick={(cit) => setActiveCitation(cit)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Hallucination Guard Telemetry */}
              {msg.role === 'assistant' && (msg.verified_ids?.length > 0 || msg.unverified_claims_removed) && (
                <div className="mt-3 pt-2.5 border-t border-slate-800/50">
                  <HallucinationBadge
                    unverifiedClaimsRemoved={msg.unverified_claims_removed}
                    verifiedIds={msg.verified_ids}
                    hallucinationsDetected={msg.hallucinations_detected}
                  />
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-3 p-4 rounded-xl bg-obsidian-850 border border-slate-800 max-w-sm glass-panel animate-pulse">
            <div className="w-3 h-3 rounded-full bg-cyber-cyan animate-ping"></div>
            <div className="text-xs font-mono text-slate-400">
              <span>Retrieving & Reranking Sovereign Threat Vectors...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form & Filters */}
      <div className="bg-obsidian-950 border border-slate-800 rounded-xl p-3 shadow-xl glass-panel">
        <div className="flex items-center justify-between mb-2 text-xs font-mono text-slate-400 px-1">
          <div className="flex items-center space-x-3">
            <span className="flex items-center space-x-1">
              <Filter className="w-3.5 h-3.5 text-cyber-indigo" />
              <span>SOURCE FILTER:</span>
            </span>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="bg-obsidian-850 border border-slate-700 rounded px-2 py-0.5 text-xs text-slate-200 focus:outline-none focus:border-cyber-cyan font-mono"
            >
              <option value="all">All Threat Feeds (NVD, MITRE, KEV, Sigma)</option>
              <option value="nvd">NVD API 2.0 (CVEs Only)</option>
              <option value="mitre">MITRE ATT&CK (Techniques Only)</option>
              <option value="cisa_kev">CISA KEV (Exploited Vulns)</option>
              <option value="sigma">SigmaHQ (Detection Rules)</option>
            </select>
          </div>

          <button
            onClick={handleResetChat}
            className="flex items-center space-x-1 text-slate-500 hover:text-slate-300 transition"
            title="Reset Conversation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Co-Pilot</span>
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
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Query sovereign cybersecurity co-pilot (e.g. 'Analyze CVE-2021-44228 impact and KEV status')..."
            className="flex-1 bg-obsidian-900 border border-slate-700/80 rounded-lg px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyber-cyan focus:ring-1 focus:ring-cyber-cyan font-sans"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyber-indigo to-indigo-600 hover:from-cyber-indigo-glow hover:to-indigo-500 text-white font-medium text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-cyber-indigo/20"
          >
            <Send className="w-4 h-4" />
            <span>Query</span>
          </button>
        </form>
      </div>

      {/* Citation Provenance Modal / Drawer */}
      <CitationDrawer
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
}
