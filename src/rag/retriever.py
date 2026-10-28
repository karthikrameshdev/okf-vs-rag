import time
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from .embedder import EmbeddingClient
from .store import QdrantVectorStore


class RAGRetrievalResult(BaseModel):
    """Result of a vector RAG retrieval."""
    query: str
    retrieval_method: str = "dense_vector_similarity_search"
    retrieved_chunks: List[Dict[str, Any]]
    context_text: str
    query_vector_sample: List[float] = Field(default_factory=list)
    vector_dimension: int = 768
    latency_breakdown: Dict[str, float]
    total_latency_ms: float
    token_estimate: int
    has_boundary_cut: bool = False
    storage_type: str = "Vector DB (HNSW Index + Dense Float Arrays + Detached Chunks)"
    auditable: bool = False


class RAGRetriever:
    """Implements classic Vector RAG retrieval pipeline."""

    def __init__(self, store: QdrantVectorStore, embedder: EmbeddingClient):
        self.store = store
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 3) -> RAGRetrievalResult:
        # Step 1: Embed the query
        t0 = time.perf_counter_ns()
        query_vec = self.embedder.embed_text(query)
        t1 = time.perf_counter_ns()
        embed_ms = (t1 - t0) / 1_000_000.0

        # Step 2: ANN Vector Search in Qdrant
        t2 = time.perf_counter_ns()
        search_hits = self.store.search(query_vec, top_k=top_k)
        t3 = time.perf_counter_ns()
        search_ms = (t3 - t2) / 1_000_000.0

        total_ms = (t3 - t0) / 1_000_000.0

        # Stitch context
        chunks_info = []
        context_parts = []
        any_boundary_cut = False

        for hit in search_hits:
            payload = hit["payload"]
            is_cut = payload.get("is_boundary_cut", False)
            if is_cut:
                any_boundary_cut = True

            chunk_repr = {
                "chunk_id": payload.get("chunk_id"),
                "source_file": payload.get("source_file"),
                "chunk_index": payload.get("chunk_index"),
                "score": round(hit["score"], 4),
                "text": payload.get("text"),
                "is_boundary_cut": is_cut,
                "vector_sample": hit.get("vector_sample", []),
            }
            chunks_info.append(chunk_repr)
            context_parts.append(
                f"--- [RAG Chunk: {chunk_repr['chunk_id']} | Cosine Similarity: {chunk_repr['score']}] ---\n"
                f"{chunk_repr['text']}"
            )

        context_text = "\n\n".join(context_parts)
        token_estimate = max(1, len(context_text) // 4)

        return RAGRetrievalResult(
            query=query,
            retrieval_method="dense_vector_similarity_search",
            retrieved_chunks=chunks_info,
            context_text=context_text,
            query_vector_sample=[round(v, 4) for v in query_vec[:8]],
            vector_dimension=len(query_vec),
            latency_breakdown={
                "embedding_latency_ms": round(embed_ms, 2),
                "vector_search_latency_ms": round(search_ms, 2),
                "total_retrieval_ms": round(total_ms, 2),
            },
            total_latency_ms=round(total_ms, 2),
            token_estimate=token_estimate,
            has_boundary_cut=any_boundary_cut,
        )
