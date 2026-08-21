import logging
import math
import os
import re
from typing import Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.config import settings
from backend.app.rag.embeddings import embedding_service

logger = logging.getLogger("aegis.rag.vector_store")

class VectorStoreManager:
    """
    Sovereign ChromaDB Persistent Vector Store Manager for AEGIS.
    Indexes documents across NVD, MITRE, CISA KEV, and Sigma sources.
    """
    def __init__(self):
        self.persist_dir = settings.CHROMA_PERSIST_DIR
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True)
        )
        self.collection_name = "aegis_threat_intel"
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=embedding_service,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def upsert_batch(self, documents: list[Any]) -> int:
        if not documents:
            return 0
            
        ids = []
        texts = []
        metadatas = []

        for doc in documents:
            if hasattr(doc, "doc_id"):
                cid = f"{doc.source}::{doc.doc_id}"
                meta = dict(doc.metadata) if isinstance(doc.metadata, dict) else {}
                meta.update({
                    "doc_id": doc.doc_id,
                    "source": doc.source,
                    "source_url": doc.source_url,
                    "fetched_at": doc.fetched_at,
                    "title": doc.title or doc.doc_id
                })
                ids.append(cid)
                texts.append(doc.content)
                metadatas.append(meta)
            elif isinstance(doc, dict):
                cid = doc.get("id") or f"{doc.get('source', 'doc')}::{doc.get('doc_id', '')}"
                ids.append(cid)
                texts.append(doc.get("content", ""))
                metadatas.append(doc.get("metadata", {}))

        if not ids:
            return 0

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"Upserted {len(ids)} documents into ChromaDB collection '{self.collection_name}'.")
        return len(ids)

    def upsert_documents(self, documents: list[Any]) -> int:
        """Alias for upsert_batch."""
        return self.upsert_batch(documents)

    def query_similar(
        self,
        query: Optional[str] = None,
        query_text: Optional[str] = None,
        top_k: int = 15,
        filter_sources: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """
        Hybrid vector + exact ID lookup.
        Ensures exact CVE-IDs and MITRE technique IDs in queries are directly retrieved.
        """
        q_str = query or query_text or ""
        where_clause = None
        if filter_sources and len(filter_sources) == 1:
            where_clause = {"source": filter_sources[0]}
        elif filter_sources and len(filter_sources) > 1:
            where_clause = {"source": {"$in": filter_sources}}

        exact_matches = []
        
        # 1. Exact ID extraction (CVEs and MITRE IDs)
        extracted_cves = re.findall(r"\bCVE-\d{4}-\d{4,7}\b", q_str, re.I)
        extracted_mitre = re.findall(r"\bT\d{4}(?:\.\d{3})?\b", q_str, re.I)
        
        for eid in (extracted_cves + extracted_mitre):
            try:
                exact_res = self.collection.get(where={"doc_id": eid.upper()})
                if not exact_res["ids"]:
                    exact_res = self.collection.get(where={"doc_id": eid})
                if exact_res and exact_res["ids"]:
                    for doc_id, doc_text, meta in zip(exact_res["ids"], exact_res["documents"], exact_res["metadatas"]):
                        exact_matches.append({
                            "id": doc_id,
                            "content": doc_text,
                            "metadata": meta,
                            "distance": 0.0,
                            "score": 0.98
                        })
            except Exception as e:
                logger.debug(f"Exact ID lookup error: {e}")

        # 2. Dense semantic vector search
        dense_matches = []
        try:
            results = self.collection.query(
                query_texts=[q_str],
                n_results=top_k,
                where=where_clause
            )
            
            if results and results["ids"] and results["ids"][0]:
                for doc_id, doc_text, meta, dist in zip(
                    results["ids"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0] if "distances" in results else [0.5] * len(results["ids"][0])
                ):
                    similarity_score = max(0.0, min(1.0, 1.0 - float(dist)))
                    dense_matches.append({
                        "id": doc_id,
                        "content": doc_text,
                        "metadata": meta,
                        "distance": dist,
                        "score": similarity_score
                    })
        except Exception as e:
            logger.error(f"Dense vector query failed: {e}")

        # Combine exact + dense (avoid duplicates)
        seen_ids = set()
        combined = []
        for doc in (exact_matches + dense_matches):
            if doc["id"] not in seen_ids:
                seen_ids.add(doc["id"])
                combined.append(doc)

        return combined[:top_k]

    def doc_exists(self, doc_id: str) -> bool:
        """Fast existence check for Hallucination Guard."""
        try:
            res = self.collection.get(where={"doc_id": doc_id.upper()}, limit=1)
            if res and res["ids"]:
                return True
            res = self.collection.get(where={"doc_id": doc_id}, limit=1)
            return bool(res and res["ids"])
        except Exception:
            return False

    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        """Retrieves single document by doc_id."""
        try:
            res = self.collection.get(where={"doc_id": doc_id.upper()}, limit=1)
            if not res or not res["ids"]:
                res = self.collection.get(where={"doc_id": doc_id}, limit=1)
            if res and res["ids"]:
                return {
                    "id": res["ids"][0],
                    "content": res["documents"][0],
                    "metadata": res["metadatas"][0]
                }
        except Exception:
            pass
        return None

    def get_stats(self) -> dict[str, Any]:
        count = self.collection.count()
        nvd_c = 0
        mitre_c = 0
        cisa_c = 0
        sigma_c = 0
        if count > 0:
            try:
                nvd_c = len(self.collection.get(where={"source": "nvd"}, limit=10000)["ids"])
                mitre_c = len(self.collection.get(where={"source": "mitre"}, limit=10000)["ids"])
                cisa_c = len(self.collection.get(where={"source": "cisa_kev"}, limit=10000)["ids"])
                sigma_c = len(self.collection.get(where={"source": "sigma"}, limit=10000)["ids"])
            except Exception:
                pass

        return {
            "total": count,
            "total_documents": count,
            "breakdown": {
                "nvd": nvd_c,
                "mitre": mitre_c,
                "cisa_kev": cisa_c,
                "sigma": sigma_c
            },
            "collection_name": self.collection_name,
            "persist_directory": self.persist_dir
        }

    def list_threat_intel(
        self,
        query_str: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        where_clause = {"source": source} if source else None
        
        if query_str and query_str.strip():
            sim = self.query_similar(query=query_str, top_k=limit, filter_sources=[source] if source else None)
            return [
                {
                    "id": d["id"],
                    "doc_id": d.get("metadata", {}).get("doc_id", d["id"]),
                    "source": d.get("metadata", {}).get("source", "nvd"),
                    "title": d.get("metadata", {}).get("title", d.get("metadata", {}).get("doc_id", d["id"])),
                    "content": d["content"],
                    "source_url": d.get("metadata", {}).get("source_url", ""),
                    "fetched_at": d.get("metadata", {}).get("fetched_at", ""),
                    "metadata": d.get("metadata", {})
                }
                for d in sim
            ]

        res = self.collection.get(
            where=where_clause,
            limit=limit,
            offset=offset,
            include=["documents", "metadatas"]
        )
        items = []
        if res and res["ids"]:
            for doc_id, doc_text, meta in zip(res["ids"], res["documents"], res["metadatas"]):
                items.append({
                    "id": doc_id,
                    "doc_id": meta.get("doc_id", doc_id),
                    "source": meta.get("source", "nvd"),
                    "title": meta.get("title", meta.get("doc_id", doc_id)),
                    "content": doc_text,
                    "source_url": meta.get("source_url", ""),
                    "fetched_at": meta.get("fetched_at", ""),
                    "metadata": meta
                })
        return items

vector_store = VectorStoreManager()
