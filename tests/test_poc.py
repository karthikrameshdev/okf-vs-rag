import pytest
from pathlib import Path
from src.config import OKF_DIR, RAW_DOCS_DIR
from src.okf.parser import parse_okf_file
from src.okf.indexer import OKFBundleIndex
from src.okf.retriever import OKFRetriever
from src.rag.chunker import chunk_documents_in_dir, chunk_text
from src.rag.embedder import EmbeddingClient
from src.rag.store import QdrantVectorStore
from src.rag.retriever import RAGRetriever
from src.llm import LLMClient
from src.comparator import BenchmarkComparator


def test_okf_parsing():
    sample_file = OKF_DIR / "services" / "payment-gateway-v2.md"
    assert sample_file.exists()
    doc = parse_okf_file(sample_file, OKF_DIR)
    assert doc.id == "payment-gateway-v2"
    assert doc.version == "2.1.0"
    assert doc.status == "production"
    assert "vault-secrets-engine" in doc.relations.get("depends_on", [])
    assert doc.verified_by is not None


def test_okf_indexer_and_retriever():
    index = OKFBundleIndex(OKF_DIR)
    assert len(index.get_all_documents()) >= 7
    assert index.get_document("payment-gateway-v2") is not None
    assert index.get_document("pci-dss-compliance") is not None

    retriever = OKFRetriever(index)
    
    # 1. Direct query
    res1 = retriever.retrieve("What authentication mechanism does payment gateway use?")
    assert "payment-gateway-v2" in res1.retrieved_entity_ids
    assert res1.latency_ms >= 0

    # 2. Relational query
    res2 = retriever.retrieve("Which services depend on Vault Secrets Engine?")
    assert "vault-secrets-engine" in res2.retrieved_entity_ids
    assert res2.retrieval_method == "deterministic_graph_traversal"


def test_rag_chunking_and_indexing():
    chunks = chunk_documents_in_dir(RAW_DOCS_DIR, chunk_size=300, overlap=50)
    assert len(chunks) > 0
    assert any(c.is_boundary_cut for c in chunks)

    embedder = EmbeddingClient()
    vec = embedder.embed_text("Test query")
    assert len(vec) == embedder.dimension

    store = QdrantVectorStore()
    vectors = embedder.embed_batch([c.text for c in chunks])
    store.index_chunks(chunks, vectors)

    retriever = RAGRetriever(store, embedder)
    res = retriever.retrieve("payment gateway authentication", top_k=2)
    assert len(res.retrieved_chunks) == 2
    assert res.total_latency_ms >= 0


def test_benchmark_comparator():
    okf_idx = OKFBundleIndex(OKF_DIR)
    okf_retriever = OKFRetriever(okf_idx)

    embedder = EmbeddingClient()
    qdrant = QdrantVectorStore()
    rag_retriever = RAGRetriever(qdrant, embedder)

    llm = LLMClient()
    comparator = BenchmarkComparator(rag_retriever, okf_retriever, llm)

    result = comparator.compare("What authentication does payment gateway use?")
    assert result.query is not None
    assert result.rag.answer is not None
    assert result.okf.answer is not None
    assert result.analysis["retrieval_speedup"] is not None
