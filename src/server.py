import os
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from src.config import OKF_DIR, RAW_DOCS_DIR, WEB_PORT, WEB_HOST
from src.okf.parser import parse_okf_file
from src.okf.indexer import OKFBundleIndex
from src.okf.retriever import OKFRetriever
from src.rag.chunker import chunk_documents_in_dir
from src.rag.embedder import EmbeddingClient
from src.rag.store import QdrantVectorStore
from src.rag.retriever import RAGRetriever
from src.llm import LLMClient
from src.comparator import BenchmarkComparator, ComparisonResult
from src.cli import SAMPLE_QUERIES

# Global instances initialized on startup
okf_index: OKFBundleIndex = None
okf_retriever: OKFRetriever = None
qdrant_store: QdrantVectorStore = None
embedder: EmbeddingClient = None
rag_retriever: RAGRetriever = None
llm: LLMClient = None
comparator: BenchmarkComparator = None


def init_pipelines():
    global okf_index, okf_retriever, qdrant_store, embedder, rag_retriever, llm, comparator

    # 1. OKF Pipeline
    okf_index = OKFBundleIndex(OKF_DIR)
    okf_retriever = OKFRetriever(okf_index)

    # 2. RAG Pipeline
    embedder = EmbeddingClient()
    qdrant_store = QdrantVectorStore()
    
    # Check if Qdrant has indexed points, if not, index them
    info = qdrant_store.get_collection_info()
    if info.get("points_count", 0) == 0:
        chunks = chunk_documents_in_dir(RAW_DOCS_DIR)
        texts = [c.text for c in chunks]
        vectors = embedder.embed_batch(texts)
        qdrant_store.index_chunks(chunks, vectors)

    rag_retriever = RAGRetriever(qdrant_store, embedder)

    # 3. LLM & Comparator
    llm = LLMClient()
    comparator = BenchmarkComparator(rag_retriever, okf_retriever, llm)


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_pipelines()
    yield

app = FastAPI(title="OKF vs RAG Architectural Comparison POC", lifespan=lifespan)


class QueryRequest(BaseModel):
    query: str


@app.get("/api/status")
def get_status() -> Dict[str, Any]:
    q_info = qdrant_store.get_collection_info() if qdrant_store else {}
    okf_docs_count = len(okf_index.get_all_documents()) if okf_index else 0
    return {
        "status": "healthy",
        "qdrant": q_info,
        "okf_documents_count": okf_docs_count,
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY")),
        "has_openrouter_key": bool(os.getenv("OPENROUTER_API_KEY")),
    }


@app.get("/api/benchmark-questions")
def get_benchmark_questions():
    return SAMPLE_QUERIES


@app.post("/api/query", response_model=ComparisonResult)
def run_query_comparison(req: QueryRequest):
    if not comparator:
        init_pipelines()
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return comparator.compare(req.query.strip())


@app.get("/api/storage/rag")
def get_rag_storage():
    """Returns stored chunks and sample vector embeddings from Qdrant."""
    if not qdrant_store:
        return []
    return qdrant_store.get_all_chunks(limit=60)


@app.get("/api/storage/okf")
def get_okf_storage():
    """Returns the OKF bundle manifest, entity documents, and directory tree."""
    if not okf_index:
        return {}
    return {
        "manifest": okf_index.manifest,
        "documents": okf_index.get_all_documents(),
        "tree": okf_index.get_bundle_tree(),
        "relations_graph": okf_index.relations_graph,
    }


# Serve static web frontend
web_dir = Path(__file__).resolve().parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return FileResponse(web_dir / "index.html")
