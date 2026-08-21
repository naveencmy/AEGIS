import logging
import time
from typing import Optional, Generator
from datetime import datetime, timezone

from backend.app.config import settings
from backend.app.models.schemas import CitationItem, QueryRequest, QueryResponse
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.reranker import reranker_service
from backend.app.rag.vector_store import vector_store
from backend.app.rag.prompt_builder import build_rag_prompt
from backend.app.rag.llm_client import llm_client
from backend.app.rag.hallucination_guard import hallucination_guard

logger = logging.getLogger("aegis.rag.engine")

class AegisRAGEngine:
    """
    Sovereign, citation-native RAG orchestration engine for AEGIS.
    Enforces 'Citation or Silence' and post-generation Hallucination Guard.
    """
    def __init__(self):
        self.db = vector_store
        self.reranker = reranker_service
        self.llm = llm_client
        self.guard = hallucination_guard

    def query(self, req: QueryRequest) -> QueryResponse:
        start_time = time.perf_counter()
        query_text = req.query.strip()
        logger.info(f"Processing AEGIS query: '{query_text[:80]}...'")

        # 1. Dense Vector Retrieval
        filter_sources = [s for s in req.filter_sources] if req.filter_sources else None
        candidates = self.db.query_similar(
            query=query_text,
            top_k=settings.RETRIEVAL_TOP_K,
            filter_sources=filter_sources
        )

        # 2. Check empty retrieval -> Silence
        if not candidates:
            logger.info("No candidates returned from vector store. Triggering Silence Response.")
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return QueryResponse(
                query=query_text,
                answer=settings.SILENCE_RESPONSE,
                citations=[],
                retrieval_confidence=0.0,
                unverified_claims_removed=False,
                verified_ids=[],
                hallucinations_detected=[],
                silence_triggered=True,
                execution_time_ms=latency_ms,
                model_used=self.llm.model_name
            )

        # 3. Local Cross-Encoder Reranking
        reranked_docs = self.reranker.rerank(
            query=query_text,
            documents=candidates,
            top_n=settings.RERANK_TOP_N
        )

        top_score = reranked_docs[0]["relevance_score"] if reranked_docs else 0.0
        min_threshold = req.min_confidence or settings.RERANK_SCORE_THRESHOLD

        logger.info(f"Top reranked intelligence relevance score: {top_score:.4f} (Threshold: {min_threshold})")

        # 4. Gating Check: Invariant 4 (CITATION OR SILENCE)
        if top_score < min_threshold:
            logger.info(f"Relevance score {top_score:.4f} below threshold {min_threshold}. Triggering sovereign silence.")
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return QueryResponse(
                query=query_text,
                answer=settings.SILENCE_RESPONSE,
                citations=[],
                retrieval_confidence=top_score,
                unverified_claims_removed=False,
                verified_ids=[],
                hallucinations_detected=[],
                silence_triggered=True,
                execution_time_ms=latency_ms,
                model_used=self.llm.model_name
            )

        # 5. Build Citation Context and Prompt
        system_prompt, user_prompt = build_rag_prompt(query_text, reranked_docs)

        # 6. Local Deterministic Generation
        raw_answer = self.llm.generate(system_prompt, user_prompt)

        # 7. Check if model naturally responded with silence
        if raw_answer.strip() == settings.SILENCE_RESPONSE or "Insufficient verified intelligence" in raw_answer:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return QueryResponse(
                query=query_text,
                answer=settings.SILENCE_RESPONSE,
                citations=[],
                retrieval_confidence=top_score,
                unverified_claims_removed=False,
                verified_ids=[],
                hallucinations_detected=[],
                silence_triggered=True,
                execution_time_ms=latency_ms,
                model_used=self.llm.model_name
            )

        # 8. Hallucination Guard: Invariant 5 (Post-generation ID extraction & DB verification)
        cited_doc_ids = {
            doc.get("metadata", {}).get("doc_id") or doc.get("doc_id")
            for doc in reranked_docs
        }
        guard_result = self.guard.validate_and_sanitize(raw_answer, cited_doc_ids)

        # 9. Format Structured Citations
        citations = []
        for doc in reranked_docs:
            meta = doc.get("metadata", {})
            doc_id = meta.get("doc_id") or doc.get("doc_id", "DOC")
            source = meta.get("source") or doc.get("source", "nvd")
            source_url = meta.get("source_url") or doc.get("source_url", "")
            fetched_at = meta.get("fetched_at") or doc.get("fetched_at", "")
            title = meta.get("title") or doc.get("title", doc_id)
            snippet = doc.get("content", "")[:300] + "..." if len(doc.get("content", "")) > 300 else doc.get("content", "")
            
            citations.append(CitationItem(
                doc_id=doc_id,
                source=source,
                source_url=source_url,
                fetched_at=fetched_at,
                title=title,
                snippet=snippet,
                relevance_score=doc.get("relevance_score", 0.0),
                metadata=meta
            ))

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return QueryResponse(
            query=query_text,
            answer=guard_result.sanitized_text,
            citations=citations,
            retrieval_confidence=top_score,
            unverified_claims_removed=guard_result.unverified_claims_removed,
            verified_ids=guard_result.verified_ids,
            hallucinations_detected=guard_result.hallucinations_detected,
            silence_triggered=False,
            execution_time_ms=latency_ms,
            model_used=self.llm.model_name
        )

rag_engine = AegisRAGEngine()
