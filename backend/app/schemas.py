from datetime import datetime
from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

SourceType = Literal["nvd", "mitre", "cisa_kev", "sigma"]

class ProvenanceMetadata(BaseModel):
    source: SourceType = Field(..., description="Canonical threat intelligence source")
    source_url: str = Field(..., description="Canonical source URL for provenance tracking")
    fetched_at: str = Field(..., description="ISO-8601 UTC timestamp of ingestion")
    doc_id: str = Field(..., description="CVE-ID, MITRE Technique ID, or Sigma Rule ID")
    title: Optional[str] = Field(None, description="Document or vulnerability title")
    severity: Optional[str] = Field(None, description="Severity rating e.g. CRITICAL, HIGH")
    tags: Optional[str] = Field(None, description="Associated tactics or categories")

class ThreatDocumentItem(BaseModel):
    doc_id: str
    source: SourceType
    source_url: str
    fetched_at: str
    title: Optional[str] = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class CVSSInfo(BaseModel):
    score: Optional[float] = Field(None, description="CVSS base score e.g. 8.6")
    severity: Optional[str] = Field(None, description="Severity e.g. CRITICAL, HIGH, MEDIUM, LOW")
    vector: Optional[str] = Field(None, description="CVSS vector string e.g. CVSS:3.1/...")

class MitreTechniqueInfo(BaseModel):
    id: str = Field(..., description="MITRE Technique ID e.g. T1611")
    name: str = Field(..., description="Technique name e.g. Escape to Host")

class CisaKevInfo(BaseModel):
    listed: bool = Field(False, description="Whether vulnerability is listed in CISA KEV")
    date_added: Optional[str] = Field(None, description="Date added to KEV catalog")
    due_date: Optional[str] = Field(None, description="Remediation due date")

class Citation(BaseModel):
    source: SourceType = Field(..., description="Intelligence source: nvd | mitre | cisa_kev | sigma")
    doc_id: str = Field(..., description="Canonical ID e.g. CVE-2024-21626 or T1611")
    source_url: str = Field(..., description="Canonical URL for provenance tracking")
    excerpt: str = Field(..., description="Verbatim text chunk used in synthesis")
    fetched_at: str = Field(..., description="ISO-8601 UTC timestamp of ingestion")

class CitationItem(BaseModel):
    doc_id: str
    source: SourceType
    source_url: str
    fetched_at: str
    title: Optional[str] = None
    snippet: str = ""
    relevance_score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

class GuardReport(BaseModel):
    ids_checked: int = Field(0, description="Total entity IDs extracted and checked")
    ids_verified: int = Field(0, description="Total entity IDs verified in ChromaDB")
    unverified_claims_removed: bool = Field(False, description="Whether fictitious claims were detected and stripped")

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=4000, description="Natural language vulnerability or threat inquiry")
    filter_sources: Optional[list[SourceType]] = Field(None, description="Optional source filter")
    min_confidence: Optional[float] = Field(None, description="Minimum relevance score threshold")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Prose answer, grounded only in retrieved docs")
    cve_ids: list[str] = Field(default_factory=list, description="Extracted and verified CVE identifiers")
    cvss: Optional[CVSSInfo] = Field(default_factory=CVSSInfo, description="CVSS vulnerability metrics")
    mitre_techniques: list[MitreTechniqueInfo] = Field(default_factory=list, description="Correlated MITRE ATT&CK techniques")
    cisa_kev: Optional[CisaKevInfo] = Field(default_factory=CisaKevInfo, description="CISA KEV exploitation metadata")
    citations: list[Citation] = Field(default_factory=list, description="Verified provenance citations")
    guard: GuardReport = Field(default_factory=GuardReport, description="Hallucination guard validation metrics")
    latency_ms: float = Field(..., description="Total execution latency in milliseconds")
    insufficient_evidence: bool = Field(False, description="True if no relevant intelligence was found (Citation or Silence)")

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=4000)
    filter_sources: Optional[list[SourceType]] = None
    min_confidence: Optional[float] = None
    stream: bool = False

class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: list[CitationItem] = Field(default_factory=list)
    retrieval_confidence: float = 0.0
    unverified_claims_removed: bool = False
    verified_ids: list[str] = Field(default_factory=list)
    hallucinations_detected: list[str] = Field(default_factory=list)
    silence_triggered: bool = False
    execution_time_ms: float = 0.0
    model_used: str = "Local Mistral"

class MatchedCVE(BaseModel):
    cve_id: str
    title: Optional[str] = None
    cvss: Optional[float] = None
    severity: Optional[str] = None
    severity_color: str = "#6b7280"
    citations: list[Citation] = Field(default_factory=list)

class ServiceScanResult(BaseModel):
    host: str
    port: int
    protocol: str = "tcp"
    service: str
    product: Optional[str] = None
    version: Optional[str] = None
    matched_cves: list[MatchedCVE] = Field(default_factory=list)

class ScannedService(BaseModel):
    port: int
    protocol: str = "tcp"
    service: str
    product: Optional[str] = None
    version: Optional[str] = None
    cpe: Optional[str] = None
    vulnerabilities: list[ChatResponse] = Field(default_factory=list)

class ScannedHost(BaseModel):
    ip: str
    hostname: Optional[str] = None
    status: str = "up"
    services: list[ScannedService] = Field(default_factory=list)

class ScanResult(BaseModel):
    hosts: list[str] = Field(default_factory=list)
    services_scanned: int = 0
    cves_found: int = 0
    results: list[ServiceScanResult] = Field(default_factory=list)
    filename: Optional[str] = "scan.xml"
    hosts_scanned: Optional[int] = 0
    services_found: Optional[int] = 0
    total_cves_matched: Optional[int] = 0
    cisa_kev_critical_alerts: Optional[int] = 0
    hosts_details: Optional[list[ScannedHost]] = Field(default_factory=list)
    parsed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

class StatsResponse(BaseModel):
    total_documents: int
    nvd_cves_count: int
    mitre_techniques_count: int
    cisa_kev_count: int
    sigma_rules_count: int
    last_ingest_time: Optional[str] = None
    vector_dimension: int = 1024
    embedding_model: str
    reranker_model: str
    llm_backend: str

class KnowledgeBaseStats(BaseModel):
    total_documents: int
    nvd_cves_count: int
    mitre_techniques_count: int
    cisa_kev_count: int
    sigma_rules_count: int
    last_ingestion_time: Optional[str] = None
    vector_dimension: int = 1024
    embedding_model: str
    reranker_model: str
    llm_backend: str

class HealthResponse(BaseModel):
    status: str = "HEALTHY"
    app_name: str
    version: str
    timestamp: str
    chroma_db_status: str
    llm_status: str
    doc_count: int

class IngestRequest(BaseModel):
    sources: Optional[list[SourceType]] = None
    limit: Optional[int] = None
    resume_checkpoint: bool = True
    force_refresh: bool = False

class IngestTaskStatus(BaseModel):
    source: SourceType
    status: Literal["idle", "running", "completed", "failed", "rate_limited"]
    records_fetched: int = 0
    records_upserted: int = 0
    current_index: int = 0
    total_available: Optional[int] = None
    last_error: Optional[str] = None
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class IngestStatusResponse(BaseModel):
    is_running: bool
    tasks: list[IngestTaskStatus]
