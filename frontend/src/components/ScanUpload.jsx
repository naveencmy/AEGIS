import React, { useState } from 'react';
import { 
  Upload, FileCode, CheckCircle2, AlertTriangle, ShieldCheck, 
  ExternalLink, Server, Globe, ShieldAlert, Cpu
} from 'lucide-react';
import { uploadNmapScan } from '../api';
import CitationCard, { CitationDrawer } from './CitationCard';
import SeverityBadge from './SeverityBadge';

export default function ScanUpload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedHost, setSelectedHost] = useState(0);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.xml')) {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Please drop a valid Nmap XML output file (.xml)');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await uploadNmapScan(file);
      setScanResult(data);
      setSelectedHost(0);
    } catch (err) {
      setError(`Upload & Parse Failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Citation Drawer Modal */}
      {selectedCitation && (
        <CitationDrawer
          citation={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}

      {/* Header */}
      <div className="p-4 rounded-xl bg-obsidian-900 border border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Server className="w-5 h-5 text-cyber-cyan" />
          <div>
            <h2 className="text-sm font-black tracking-wider text-white font-mono uppercase">
              Sovereign Nmap Telemetry & CVE Surface Analyzer
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              Upload real Nmap XML scans (-sV -oX) to correlate open network services against ChromaDB threat intelligence
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center space-x-2 text-xs font-mono text-emerald-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Real-Data Grounding Only</span>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="p-6 rounded-xl bg-obsidian-900 border border-slate-800 space-y-4 shadow-xl">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
            dragOver 
              ? 'border-cyber-cyan bg-cyber-cyan/10' 
              : 'border-slate-750 hover:border-slate-600 bg-obsidian-950/60'
          }`}
          onClick={() => document.getElementById('nmap-file-input').click()}
        >
          <input
            id="nmap-file-input"
            type="file"
            accept=".xml"
            onChange={handleFileChange}
            className="hidden"
          />
          <Upload className="w-8 h-8 text-cyber-cyan mx-auto mb-2 opacity-80" />
          <p className="text-xs font-bold text-white font-mono">
            {file ? file.name : "Drag & drop Nmap scan.xml here, or click to browse"}
          </p>
          <p className="text-[11px] text-slate-500 mt-1 font-mono">
            Supported command: nmap -sV -oX scan.xml &lt;target&gt;
          </p>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="text-xs font-mono text-slate-400">
            {file ? (
              <span className="text-cyber-cyan">Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
            ) : (
              <span>Ready for XML upload</span>
            )}
          </div>
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className={`px-6 py-2.5 rounded-lg text-xs font-bold font-mono transition-all flex items-center space-x-2 ${
              !file || loading
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-cyber-indigo hover:bg-cyber-indigo-glow text-white shadow-lg shadow-cyber-indigo/30'
            }`}
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Correlating ChromaDB CVEs...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4" />
                <span>Run Sovereign Surface Analysis</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Results View */}
      {scanResult && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-obsidian-900 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-mono">HOSTS DISCOVERED</span>
              <p className="text-2xl font-black text-white mt-1">{scanResult.hosts?.length || scanResult.hosts_scanned || 0}</p>
            </div>
            <div className="p-4 rounded-xl bg-obsidian-900 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-mono">SERVICES SCANNED</span>
              <p className="text-2xl font-black text-cyber-cyan mt-1">{scanResult.services_scanned || scanResult.services_found || 0}</p>
            </div>
            <div className="p-4 rounded-xl bg-obsidian-900 border border-slate-800">
              <span className="text-[11px] text-slate-400 font-mono">MATCHED CVES</span>
              <p className="text-2xl font-black text-cyber-indigo-glow mt-1">{scanResult.cves_found || scanResult.total_cves_matched || 0}</p>
            </div>
            <div className="p-4 rounded-xl bg-obsidian-900 border border-red-900/60 bg-red-950/20">
              <span className="text-[11px] text-red-400 font-mono">CISA KEV ALERTS</span>
              <p className="text-2xl font-black text-red-400 mt-1">{scanResult.cisa_kev_critical_alerts || 0}</p>
            </div>
          </div>

          {/* Results Table & Details */}
          <div className="p-5 rounded-xl bg-obsidian-900 border border-slate-800 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-cyber-cyan" />
                <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  Network Service Vulnerability Surface Matrix
                </h3>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                Target: {scanResult.hosts?.join(', ')}
              </span>
            </div>

            {/* Service Rows */}
            <div className="space-y-4">
              {scanResult.results?.map((res, idx) => (
                <div key={idx} className="p-4 rounded-lg bg-obsidian-850 border border-slate-800 space-y-3">
                  {/* Service Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-1 rounded bg-obsidian-950 text-white font-mono text-xs font-bold border border-slate-750">
                        {res.port}/{res.protocol}
                      </span>
                      <span className="font-bold text-xs text-cyber-cyan font-mono">{res.service}</span>
                      {res.product && (
                        <span className="text-xs text-slate-300 font-sans">
                          {res.product} {res.version}
                        </span>
                      )}
                    </div>

                    <div>
                      {res.matched_cves?.length > 0 ? (
                        <span className="px-2.5 py-0.5 rounded bg-red-950 text-red-400 border border-red-800 font-mono text-[11px] font-bold">
                          {res.matched_cves.length} MATCHED CVES
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[11px]">
                          NO MATCHED CVES
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Matched CVEs Grid */}
                  {res.matched_cves?.length > 0 ? (
                    <div className="space-y-2.5 pt-1">
                      {res.matched_cves.map((cve, cIdx) => (
                        <div key={cIdx} className="p-3 rounded bg-obsidian-950 border border-slate-800 space-y-2 text-xs">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center space-x-2">
                              <span className="font-mono font-bold text-white text-xs bg-obsidian-800 px-2 py-0.5 rounded border border-slate-700">
                                {cve.cve_id}
                              </span>
                              {cve.cvss && (
                                <SeverityBadge score={cve.cvss} severity={cve.severity} />
                              )}
                              {cve.severity === 'CRITICAL_EXPLOITED' && (
                                <span className="px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-mono text-[10px] font-bold">
                                  ACTIVE IN CISA KEV
                                </span>
                              )}
                            </div>
                            <span className="text-slate-400 font-sans text-xs truncate max-w-md">
                              {cve.title}
                            </span>
                          </div>

                          {/* Citations for CVE */}
                          {cve.citations?.length > 0 && (
                            <div className="pt-2 border-t border-slate-850">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                {cve.citations.map((cit, citIdx) => (
                                  <CitationCard 
                                    key={citIdx} 
                                    citation={cit} 
                                    onClick={(c) => setSelectedCitation(c)}
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 font-mono italic">
                      No verified vulnerabilities found in local knowledge base for this service banner.
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
