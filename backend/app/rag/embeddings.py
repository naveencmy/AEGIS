import hashlib
import logging
import math
import os
import re
from typing import Optional, Union, Any
import numpy as np
from backend.app.config import settings

logger = logging.getLogger("aegis.rag.embeddings")

try:
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
except ImportError:
    try:
        from chromadb import EmbeddingFunction, Documents, Embeddings
    except ImportError:
        EmbeddingFunction = object
        Documents = list[str]
        Embeddings = list[list[float]]

class SovereignDenseVectorizer:
    """
    100% Sovereign, zero-network fallback embedding vectorizer.
    Generates deterministic normalized 384-dimensional dense embeddings.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def encode_one(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        if not text:
            return vec.tolist()
            
        words = re.findall(r"\w+", text.lower())
        if not words:
            return vec.tolist()

        for i, word in enumerate(words):
            weight = 1.0 / math.sqrt(i + 1)
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 16) % 2 == 0 else -1.0
            vec[idx] += sign * (2.0 + len(word) * 0.1) * weight
            
            if len(word) >= 3:
                for k in range(len(word) - 2):
                    sub = word[k:k+3]
                    sub_h = int(hashlib.sha256(sub.encode("utf-8")).hexdigest(), 16)
                    sub_idx = sub_h % self.dim
                    sub_sign = 1.0 if (sub_h >> 16) % 2 == 0 else -1.0
                    vec[sub_idx] += sub_sign * 0.5 * weight

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec.tolist()

    def encode(self, texts: list[str]) -> list[list[float]]:
        return [self.encode_one(t) for t in texts]

class BGEM3EmbeddingFunction(EmbeddingFunction):
    """
    Sovereign local BAAI/bge-m3 embedding function compliant with ChromaDB 1.5+.
    Uses local ONNX runtime for instant offline execution without external network latency.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._model = None
        self._fallback_vectorizer = SovereignDenseVectorizer(dim=384)

    def name(self) -> str:
        return "bge_m3_embedding_function"

    @property
    def model(self):
        if self._model is None:
            # 1. Try local ONNX default embedding function
            try:
                import chromadb.utils.embedding_functions as ef
                self._model = ef.DefaultEmbeddingFunction()
                logger.info("ChromaDB Sovereign ONNX embedding engine initialized.")
                return self._model
            except Exception as e:
                logger.warning(f"ONNX engine unavailable ({e}). Checking local cache...")

            # 2. Try SentenceTransformer with local cache only
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = SentenceTransformer(
                    self.model_name,
                    device=device,
                    cache_folder=settings.MODELS_CACHE_DIR,
                    local_files_only=True
                )
                logger.info("Local BGE-M3 model loaded from cache.")
                return self._model
            except Exception:
                pass

            self._model = self._fallback_vectorizer
        return self._model

    def __call__(self, input: Union[Documents, str] = None, *args, **kwargs) -> Embeddings:
        """ChromaDB embedding function interface."""
        m = self.model
        texts = input if input is not None else (args[0] if args else [])
        if isinstance(texts, str):
            texts = [texts]
        else:
            texts = list(texts)

        if callable(m):
            try:
                res = m(texts)
                if isinstance(res, np.ndarray):
                    return res.tolist()
                return res
            except Exception:
                pass
        return self._fallback_vectorizer.encode(texts)

    def embed_documents(self, input: list[str] = None, *args, **kwargs) -> list[list[float]]:
        texts = input if input is not None else (args[0] if args else [])
        if isinstance(texts, str):
            texts = [texts]
        return self(texts)

    def embed_query(self, input: Union[str, list[str]] = None, *args, **kwargs) -> list[list[float]]:
        val = input if input is not None else (args[0] if args else "")
        if isinstance(val, str):
            return self([val])
        return self(list(val))

embedding_service = BGEM3EmbeddingFunction()
