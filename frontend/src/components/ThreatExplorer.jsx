import React, { useState, useEffect } from 'react';
import { Search, Filter, Database, ExternalLink, Shield, RefreshCw, FileText, ChevronRight } from 'lucide-react';
import { searchThreatIntel } from '../services/api';
import { CitationDrawer } from './CitationCard';

const sourceColors = {
  nvd: 'bg-indigo-950/80 border-indigo-700/60 text-indigo-300',
  mitre: 'bg-purple-950/80 border-purple-700/60 text-purple-300',
  cisa_kev: 'bg-rose-950/80 border-rose-700/60 text-rose-300',
  sigma: 'bg-emerald-950/80 border-emerald-700/60 text-emerald-300',
};

export default function ThreatExplorer({ kbStats }) {
  const [query, setQuery] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeDoc, setActiveDoc] = useState(null);

  const fetchResults = async () => {
    setIsLoading(true);
    try {
      const data = await searchThreatIntel(query, selectedSource || null, 60);
      setResults(data || []);
    } catch (err) {
      console.error('Failed to search threat intelligence:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [selectedSource]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchResults();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Search and Filters Header */}
      <div className="bg-obsidian-850 border border-slate-800 rounded-xl p-5 mb-6 glass-panel">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Database className="w-5 h-5 text-cyber-cyan" />
              <span>Sovereign Threat Intelligence Matrix</span>
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Browse and verify live indexed records across NVD, MITRE ATT&CK, CISA KEV, and Sigma rules.
            </p>
          </div>

          <button
            onClick={fetchResults}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-obsidian-800 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Index</span>
          </button>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex items-center space-x-3 mb-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by CVE ID, MITRE technique (e.g. T1059), vendor, or attack tactic..."
              className="w-full bg-obsidian-950 border border-slate-700/80 rounded-lg pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyber-cyan font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-2 rounded-lg bg-cyber-indigo hover:bg-cyber-indigo-glow text-white text-xs font-mono font-bold transition shadow-md shadow-cyber-indigo/20"
          >
            Search
          </button>
        </form>

        {/* Source Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <span className="text-slate-500 mr-1 flex items-center space-x-1">
            <Filter className="w-3 h-3 text-slate-500" />
            <span>SOURCE:</span>
          </span>

          {[
            { key: '', label: 'All Feeds', count: kbStats?.total_documents },
            { key: 'cisa_kev', label: 'CISA KEV', count: kbStats?.cisa_kev_count },
            { key: 'mitre', label: 'MITRE ATT&CK', count: kbStats?.mitre_techniques_count },
            { key: 'sigma', label: 'SigmaHQ Rules', count: kbStats?.sigma_rules_count },
            { key: 'nvd', label: 'NVD API 2.0', count: kbStats?.nvd_cves_count },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setSelectedSource(tab.key)}
              className={`px-3 py-1 rounded-md transition border ${
                selectedSource === tab.key
                  ? 'bg-cyber-cyan/20 border-cyber-cyan text-cyber-cyan-glow font-bold'
                  : 'bg-obsidian-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className="ml-1.5 text-[10px] opacity-70">({tab.count})</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Results Matrix Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center space-y-3 text-slate-400 font-mono text-xs">
            <div className="w-8 h-8 rounded-full border-2 border-cyber-cyan border-t-transparent animate-spin"></div>
            <span>Searching Sovereign Vector Index...</span>
          </div>
        </div>
      ) : results.length === 0 ? (
        <div className="bg-obsidian-850 border border-slate-800 rounded-xl p-12 text-center text-slate-400 font-mono text-xs glass-panel">
          <FileText className="w-8 h-8 mx-auto mb-3 text-slate-600" />
          <p className="text-slate-300 font-bold mb-1">No Threat Intelligence Records Found</p>
          <p className="text-slate-500">
            Try adjusting your search keywords or sync more live records from the Ingestion tab.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {results.map((item, idx) => {
            const source = item.source || item.metadata?.source || 'nvd';
            const colorClass = sourceColors[source] || 'bg-slate-800 border-slate-700 text-slate-300';
            const docId = item.doc_id || item.metadata?.doc_id || `DOC-${idx}`;
            const title = item.title || item.metadata?.title || docId;
            const sourceUrl = item.source_url || item.metadata?.source_url || '';
            const fetchedAt = item.fetched_at || item.metadata?.fetched_at || '';

            return (
              <div
                key={idx}
                className="bg-obsidian-850 border border-slate-800 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition glass-card group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold border ${colorClass}`}>
                      {source.toUpperCase()}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500 truncate max-w-[140px]">
                      {fetchedAt ? fetchedAt.split('T')[0] : ''}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white font-mono mb-1.5 group-hover:text-cyber-cyan transition">
                    {docId}
                  </h3>

                  <p className="text-xs text-slate-300 font-sans font-medium line-clamp-1 mb-2">
                    {title}
                  </p>

                  <p className="text-xs text-slate-400 font-mono line-clamp-3 leading-relaxed mb-4">
                    {item.content || item.snippet || ''}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
                  {sourceUrl ? (
                    <a
                      href={sourceUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-cyber-cyan hover:underline flex items-center space-x-1"
                    >
                      <span>Source Link</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span></span>
                  )}

                  <button
                    onClick={() =>
                      setActiveDoc({
                        doc_id: docId,
                        title: title,
                        source: source,
                        source_url: sourceUrl,
                        fetched_at: fetchedAt,
                        snippet: item.content || item.snippet || '',
                        relevance_score: item.similarity_score || item.relevance_score || 1.0,
                        metadata: item.metadata || {},
                      })
                    }
                    className="flex items-center space-x-1 text-slate-400 hover:text-white transition"
                  >
                    <span>View Provenance</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Slide-out Drawer */}
      <CitationDrawer citation={activeDoc} onClose={() => setActiveDoc(null)} />
    </div>
  );
}
