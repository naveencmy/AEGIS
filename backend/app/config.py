from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    # App Information
    APP_NAME: str = "AEGIS - Sovereign Cybersecurity Co-Pilot"
    APP_VERSION: str = "0.1.0"
    CORS_ORIGINS: list[str] = ["*"]

    # Base Directories
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    BACKEND_DIR: Path = Path(__file__).resolve().parent.parent
    CHECKPOINT_DIR: Path = Path(__file__).resolve().parent.parent / "checkpoints"

    # Ingestion Live URLs
    NVD_API_URL: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    CISA_KEV_URL: str = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    MITRE_ATTACK_URL: str = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
    SIGMA_REPO_URL: str = "https://github.com/SigmaHQ/sigma.git"
    SIGMA_RULES_ZIP: str = "https://github.com/SigmaHQ/sigma/archive/refs/heads/master.zip"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = str(Path(__file__).resolve().parent.parent / "data" / "chroma")
    COLLECTION_UNIFIED: str = "aegis_intel_unified"
    COLLECTION_NVD: str = "aegis_intel_nvd"
    COLLECTION_MITRE: str = "aegis_intel_mitre"
    COLLECTION_KEV: str = "aegis_intel_cisa_kev"
    COLLECTION_SIGMA: str = "aegis_intel_sigma"

    # Embedding & Reranking Models
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    RETRIEVAL_TOP_K: int = 15
    RERANK_TOP_N: int = 5
    RERANK_SCORE_THRESHOLD: float = 0.35

    # LLM Settings (Mistral-7B Q4 via Ollama / Sovereign Engine)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "mistral:7b-instruct-q4_K_M"
    TEMPERATURE: float = 0.1
    TOP_P: float = 0.9
    FIXED_SEED: int = 42

    # Ingestion Policies
    NVD_RATE_LIMIT_DELAY: float = 6.0
    MAX_INGESTION_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0

    # Invariant 4 - Sovereign Silence Message
    SILENCE_RESPONSE: str = "Insufficient verified intelligence in the knowledge base"

settings = Settings()
