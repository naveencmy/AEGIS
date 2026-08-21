import argparse
import logging
import sys
import time
import re
from pathlib import Path
from typing import Optional, Any

# Ensure backend root on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.config import settings
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.reranker import reranker_service

logger = logging.getLogger("aegis.rag.vectorstore")

COLLECTION_MAP = {
    "nvd": "cves",
    "cves": "cves",
    "mitre": "mitre_techniques",
    "mitre_techniques": "mitre_techniques",
    "kev": "kev",
    "cisa_kev": "kev",
    "sigma": "sigma_rules",
    "sigma_rules": "sigma_rules"
}

class SovereignVectorStore:
    """
    ChromaDB Persistent Store with 4 dedicated collections:
    - cves (NVD)
    - mitre_techniques (MITRE ATT&CK)
    - kev (CISA KEV)
    - sigma_rules (SigmaHQ)
    Plus unified collection support and multi-collection dense retrieval.
    """
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = Path(persist_dir or settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_fn = embedding_service

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True)
        )

        # 4 Core Collections
        self.collections = {
            "cves": self.client.get_or_create_collection(
                name="cves",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            ),
            "mitre_techniques": self.client.get_or_create_collection(
                name="mitre_techniques",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            ),
            "kev": self.client.get_or_create_collection(
                name="kev",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            ),
            "sigma_rules": self.client.get_or_create_collection(
                name="sigma_rules",
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            ),
            "unified": self.client.get_or_create_collection(
                name=settings.COLLECTION_UNIFIED,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
        }

    @property
    def collection(self):
        """Backward-compatible collection accessor."""
        return self.collections.get("unified")

    def upsert_documents(self, documents: list[dict[str, Any]], source: str = "nvd"):
        if not documents:
            return

        ids = [doc["id"] for doc in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        col_key = COLLECTION_MAP.get(source.lower(), "cves")
        col = self.collections[col_key]

        col.upsert(ids=ids, documents=texts, metadatas=metadatas)
        self.collections["unified"].upsert(ids=ids, documents=texts, metadatas=metadatas)

        logger.info(f"Upserted {len(documents)} documents into '{col_key}' & 'unified'.")

    def query(self, query_text: str, sources: Optional[list[str]] = None, k: int = 8) -> list[dict[str, Any]]:
        """
        Dense semantic retrieval across collections with exact entity targeting.
        """
        results = []
        target_cols = []

        if sources:
            for s in sources:
                ck = COLLECTION_MAP.get(s.lower())
                if ck and ck in self.collections and ck not in target_cols:
                    target_cols.append(ck)
        
        if not target_cols:
            target_cols = ["cves", "mitre_techniques", "kev", "sigma_rules"]

        # Exact ID pre-fetch
        exact_cves = re.findall(r"\bCVE-\d{4}-\d{4,7}\b", query_text, re.I)
        exact_mitre = re.findall(r"\bT\d{4}(?:\.\d{3})?\b", query_text, re.I)

        seen_ids = set()

        if exact_cves:
            for cid in exact_cves:
                for ck in ["cves", "kev", "unified"]:
                    try:
                        exact_res = self.collections[ck].get(
                            ids=[f"nvd::{cid.upper()}", f"cisa_kev::{cid.upper()}", cid.upper()],
                            include=["documents", "metadatas"]
                        )
                        if exact_res and exact_res.get("ids"):
                            for eid, doc_text, meta in zip(exact_res["ids"], exact_res["documents"], exact_res["metadatas"]):
                                if eid not in seen_ids:
                                    seen_ids.add(eid)
                                    results.append({
                                        "id": eid,
                                        "doc_id": meta.get("doc_id", eid),
                                        "source": meta.get("source", ck),
                                        "content": doc_text,
                                        "metadata": meta,
                                        "distance": 0.01,
                                        "similarity": 0.995
                                    })
                    except Exception:
                        pass

        if exact_mitre:
            for tid in exact_mitre:
                try:
                    exact_res = self.collections["mitre_techniques"].get(
                        ids=[f"mitre::{tid.upper()}", tid.upper()],
                        include=["documents", "metadatas"]
                    )
                    if exact_res and exact_res.get("ids"):
                        for eid, doc_text, meta in zip(exact_res["ids"], exact_res["documents"], exact_res["metadatas"]):
                            if eid not in seen_ids:
                                seen_ids.add(eid)
                                results.append({
                                    "id": eid,
                                    "doc_id": meta.get("doc_id", eid),
                                    "source": "mitre",
                                    "content": doc_text,
                                    "metadata": meta,
                                    "distance": 0.01,
                                    "similarity": 0.995
                                })
                except Exception:
                    pass

        k_per_col = max(3, (k // len(target_cols)) + 2)

        for ck in target_cols:
            col = self.collections[ck]
            count = col.count()
            if count == 0:
                continue
            
            try:
                res = col.query(
                    query_texts=[query_text],
                    n_results=min(k_per_col, count),
                    include=["documents", "metadatas", "distances"]
                )
                
                if res and res.get("documents") and res["documents"][0]:
                    docs = res["documents"][0]
                    metas = res["metadatas"][0] if res.get("metadatas") else [{}] * len(docs)
                    dists = res["distances"][0] if res.get("distances") else [0.0] * len(docs)
                    ids = res["ids"][0] if res.get("ids") else [""] * len(docs)

                    for did, content, meta, dist in zip(ids, docs, metas, dists):
                        if did not in seen_ids:
                            seen_ids.add(did)
                            results.append({
                                "id": did,
                                "doc_id": meta.get("doc_id", did),
                                "source": meta.get("source", ck),
                                "content": content,
                                "metadata": meta,
                                "distance": dist,
                                "similarity": round(1.0 - (dist / 2.0 if dist <= 2.0 else 0.0), 4)
                            })
            except Exception as e:
                logger.error(f"Error querying collection '{ck}': {e}")

        # Sort by distance ascending
        results.sort(key=lambda x: x.get("distance", 1.0))
        return results[:k]

    def query_similar(self, query: str, top_k: int = 8, filter_sources: Optional[list[str]] = None) -> list[dict[str, Any]]:
        return self.query(query_text=query, sources=filter_sources, k=top_k)

    def get_stats(self) -> dict[str, Any]:
        counts = {
            "cves": self.collections["cves"].count(),
            "mitre_techniques": self.collections["mitre_techniques"].count(),
            "kev": self.collections["kev"].count(),
            "sigma_rules": self.collections["sigma_rules"].count(),
            "unified": self.collections["unified"].count()
        }
        total = sum(counts[k] for k in ["cves", "mitre_techniques", "kev", "sigma_rules"])
        return {
            "total_documents": total,
            "collections": counts,
            "breakdown": {
                "nvd": counts["cves"],
                "mitre": counts["mitre_techniques"],
                "cisa_kev": counts["kev"],
                "sigma": counts["sigma_rules"]
            },
            "persist_directory": str(self.persist_dir)
        }

vector_store = SovereignVectorStore()

def main():
    parser = argparse.ArgumentParser(description="AEGIS ChromaDB Sovereign Vector Store CLI")
    parser.add_argument("--query", type=str, required=True, help="Search query string")
    parser.add_argument("--sources", nargs="+", default=None, help="Filter by sources (cves, mitre, kev, sigma)")
    parser.add_argument("--top_k", type=int, default=8, help="Number of dense retrieval candidates")
    parser.add_argument("--top_n", type=int, default=4, help="Number of reranked results to display")
    parser.add_argument("--stats", action="store_true", help="Print collection statistics")
    args = parser.parse_args()

    if args.stats:
        stats = vector_store.get_stats()
        print("\n=== ChromaDB Collection Statistics ===")
        for k, v in stats["collections"].items():
            print(f"  Collection: {k:<18} Count: {v:,}")
        print(f"  Total Verified Docs: {stats['total_documents']:,}\n")

    print(f"\n[QUERY]: '{args.query}'")
    start = time.perf_counter()
    candidates = vector_store.query(query_text=args.query, sources=args.sources, k=args.top_k)
    retrieve_ms = (time.perf_counter() - start) * 1000.0

    print(f"[DENSE RETRIEVAL]: Found {len(candidates)} candidates ({retrieve_ms:.2f}ms)")
    
    start = time.perf_counter()
    reranked = reranker_service.rerank(args.query, candidates, top_n=args.top_n)
    rerank_ms = (time.perf_counter() - start) * 1000.0

    print(f"\n=== Top-{len(reranked)} Reranked Intelligence Briefs ({rerank_ms:.2f}ms) ===")
    for idx, doc in enumerate(reranked, 1):
        meta = doc.get("metadata", {})
        doc_id = meta.get("doc_id", doc.get("id"))
        src = meta.get("source", doc.get("source", "UNKNOWN")).upper()
        score = doc.get("relevance_score", 0.0)
        title = meta.get("title", doc_id)
        print(f"[{idx}] {doc_id} ({src}) - Score: {score:.4f}")
        print(f"    Title: {title}")
        print(f"    Snippet: {doc.get('content', '')[:160]}...\n")

if __name__ == "__main__":
    main()
