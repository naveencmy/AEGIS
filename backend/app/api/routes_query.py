import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from backend.app.models.schemas import QueryRequest, QueryResponse
from backend.app.rag.engine import rag_engine

logger = logging.getLogger("aegis.api.query")
router = APIRouter(prefix="/api/v1", tags=["Query & Reasoning"])

@router.post("/query", response_model=QueryResponse, summary="Execute Sovereign Grounded Query")
async def execute_query(req: QueryRequest):
    """
    Executes grounded cybersecurity query with dense retrieval, cross-encoder reranking,
    Citation or Silence threshold gating, local Mistral 7B inference, and Hallucination Guard.
    """
    try:
        response = rag_engine.query(req)
        return response
    except Exception as e:
        logger.exception(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@router.post("/query/stream", summary="Stream Sovereign Grounded Query")
async def execute_query_stream(req: QueryRequest):
    """
    Streams response tokens using Server-Sent Events (SSE) while enforcing provenance citations and gating.
    """
    def event_generator():
        try:
            # Run query through RAG engine
            res = rag_engine.query(req)
            
            # Send metadata header first
            meta = {
                "type": "metadata",
                "citations": [c.model_dump() for c in res.citations],
                "retrieval_confidence": res.retrieval_confidence,
                "silence_triggered": res.silence_triggered,
                "verified_ids": res.verified_ids,
                "hallucinations_detected": res.hallucinations_detected,
                "unverified_claims_removed": res.unverified_claims_removed,
                "execution_time_ms": res.execution_time_ms
            }
            yield f"data: {json.dumps(meta)}\n\n"
            
            # Stream answer words
            words = res.answer.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                data = {"type": "token", "content": chunk}
                yield f"data: {json.dumps(data)}\n\n"
                
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
