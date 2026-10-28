import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from src.config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
from .chunker import TextChunk

logger = logging.getLogger("RAGStore")


class QdrantVectorStore:
    """Manages the Qdrant Vector Database connection, collections, and point indexing."""

    def __init__(
        self,
        host: str = QDRANT_HOST,
        port: int = QDRANT_PORT,
        collection_name: str = QDRANT_COLLECTION,
        dimension: int = 768,
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.is_docker = False
        self.client = self._connect()
        self._ensure_collection()

    def _connect(self) -> QdrantClient:
        """Connects to Docker Qdrant instance, falling back to embedded memory mode if needed."""
        try:
            client = QdrantClient(host=self.host, port=self.port, timeout=3.0, check_compatibility=False)
            # Ping
            client.get_collections()
            self.is_docker = True
            logger.info("Connected successfully to Qdrant Docker container on port %s", self.port)
            return client
        except Exception as e:
            logger.warning("Could not reach Docker Qdrant at %s:%s (%s). Using embedded local Qdrant engine.", self.host, self.port, e)
            self.is_docker = False
            return QdrantClient(location=":memory:", check_compatibility=False)

    def _ensure_collection(self):
        """Creates the vector collection if it doesn't already exist."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.dimension,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def reset_collection(self):
        """Clears and re-creates collection."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._ensure_collection()

    def index_chunks(self, chunks: List[TextChunk], vectors: List[List[float]]):
        """Indexes text chunks with their dense vector embeddings into Qdrant."""
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append(
                qmodels.PointStruct(
                    id=i + 1,
                    vector=vector,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "source_file": chunk.source_file,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                        "is_boundary_cut": chunk.is_boundary_cut,
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(self, query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Performs Approximate Nearest Neighbor (ANN) search in Qdrant."""
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=True,
        )

        results = []
        for scored_point in search_result.points:
            results.append({
                "point_id": scored_point.id,
                "score": scored_point.score,
                "payload": scored_point.payload,
                "vector_sample": scored_point.vector[:8] if scored_point.vector else [],
                "vector_dimension": len(scored_point.vector) if scored_point.vector else self.dimension,
            })
        return results

    def get_collection_info(self) -> Dict[str, Any]:
        """Returns statistics about the vector store."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "status": str(info.status),
                "points_count": info.points_count,
                "vectors_count": getattr(info, "vectors_count", info.points_count),
                "indexed_vectors_count": getattr(info, "indexed_vectors_count", info.points_count),
                "vector_dimension": self.dimension,
                "distance_metric": "Cosine",
                "backend": "Docker Qdrant Container" if self.is_docker else "Embedded In-Memory Qdrant",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_all_chunks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves stored chunks and sample vector embeddings for user inspection."""
        try:
            records, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=True,
            )
            data = []
            for r in records:
                data.append({
                    "point_id": r.id,
                    "payload": r.payload,
                    "vector_sample": r.vector[:6] if r.vector else [],
                    "vector_dimension": len(r.vector) if r.vector else self.dimension,
                })
            return data
        except Exception:
            return []
