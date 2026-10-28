import os
import sys
import argparse
import uvicorn
from rich.console import Console
from rich.panel import Panel

from src.config import OKF_DIR, RAW_DOCS_DIR, WEB_PORT, WEB_HOST
from src.okf.indexer import OKFBundleIndex
from src.okf.retriever import OKFRetriever
from src.rag.chunker import chunk_documents_in_dir
from src.rag.embedder import EmbeddingClient
from src.rag.store import QdrantVectorStore
from src.rag.retriever import RAGRetriever
from src.llm import LLMClient
from src.comparator import BenchmarkComparator
from src.cli import run_cli_interactive, display_comparison, SAMPLE_QUERIES, BANNER

console = Console()


def provision_and_index():
    """Initializes OKF bundle and indexes RAG raw documents into Qdrant."""
    console.print("[bold cyan]🔄 Initializing Open Knowledge Format (OKF) index...[/bold cyan]")
    okf_idx = OKFBundleIndex(OKF_DIR)
    console.print(f"  [green]✓[/green] Indexed {len(okf_idx.get_all_documents())} OKF markdown documents.")

    console.print("[bold cyan]🔄 Connecting to Qdrant Vector Database...[/bold cyan]")
    embedder = EmbeddingClient()
    qdrant = QdrantVectorStore()
    
    info = qdrant.get_collection_info()
    console.print(f"  [green]✓[/green] Storage Engine: [bold white]{info.get('backend')}[/bold white]")

    if info.get("points_count", 0) == 0:
        console.print("[bold cyan]🔄 Chunking raw documents & indexing embeddings into Qdrant...[/bold cyan]")
        chunks = chunk_documents_in_dir(RAW_DOCS_DIR)
        texts = [c.text for c in chunks]
        vectors = embedder.embed_batch(texts)
        qdrant.index_chunks(chunks, vectors)
        console.print(f"  [green]✓[/green] Successfully indexed {len(chunks)} chunks into collection '{qdrant.collection_name}'.")
    else:
        console.print(f"  [green]✓[/green] Collection '{qdrant.collection_name}' already populated ({info.get('points_count')} points).")

    okf_retriever = OKFRetriever(okf_idx)
    rag_retriever = RAGRetriever(qdrant, embedder)
    llm = LLMClient()
    comparator = BenchmarkComparator(rag_retriever, okf_retriever, llm)

    return comparator


def run_automated_benchmark(comparator: BenchmarkComparator):
    """Executes a sample benchmark comparison and displays side-by-side metrics."""
    console.print(BANNER)
    console.print(Panel(
        "[bold white]Running Initial Benchmark Comparison:[/bold white]\n"
        "[dim]Comparing how RAG and OKF handle legacy version collision & authentication policies[/dim]",
        border_style="yellow"
    ))

    # Benchmark Query 1
    sample = SAMPLE_QUERIES[0]
    result = comparator.compare(sample["query"])
    display_comparison(result)


def main():
    parser = argparse.ArgumentParser(description="OKF vs RAG Architectural Comparison POC")
    parser.add_argument(
        "--mode",
        choices=["cli", "server", "benchmark", "all"],
        default="all",
        help="Run mode: 'cli' (terminal only), 'server' (web UI), 'benchmark' (run comparison report), 'all' (run comparison report + interactive CLI and web server)",
    )
    parser.add_argument("--port", type=int, default=WEB_PORT, help="Port for web dashboard")
    args = parser.parse_args()

    comparator = provision_and_index()

    if args.mode == "benchmark":
        run_automated_benchmark(comparator)
        sys.exit(0)

    elif args.mode == "cli":
        run_automated_benchmark(comparator)
        run_cli_interactive(comparator)

    elif args.mode == "server":
        console.print(f"\n[bold green]🚀 Web Dashboard live at: [underline]http://localhost:{args.port}[/underline][/bold green]\n")
        uvicorn.run("src.server:app", host=WEB_HOST, port=args.port, log_level="info")

    elif args.mode == "all":
        # Run benchmark in console, then start server with link, or interactive CLI
        run_automated_benchmark(comparator)
        console.print(f"\n[bold green]🌐 Starting Web UI at: [underline]http://localhost:{args.port}[/underline][/bold green]")
        console.print("[dim cyan]Launching interactive terminal benchmark loop...[/dim cyan]\n")
        
        # Start server in background thread or prompt user
        import threading
        config = uvicorn.Config("src.server:app", host=WEB_HOST, port=args.port, log_level="warning")
        server = uvicorn.Server(config)
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()

        console.print(f"[bold cyan]✓ Web UI is active in the background at [underline]http://localhost:{args.port}[/underline][/bold cyan]")
        run_cli_interactive(comparator)


if __name__ == "__main__":
    main()
