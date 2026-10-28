import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.layout import Layout
from rich.prompt import Prompt
from rich.text import Text
from rich import box

from src.comparator import BenchmarkComparator, ComparisonResult

console = Console()

BANNER = """
[bold cyan]╔══════════════════════════════════════════════════════════════════════════╗
║        [bold white]OKF (Open Knowledge Format)[/bold white] [bold yellow]vs[/bold yellow] [bold magenta]RAG (Retrieval-Augmented Generation)[/bold magenta]       ║
║     [dim]Architectural Comparison POC: Storage, Latency, Provenance & Graph[/dim]   ║
╚══════════════════════════════════════════════════════════════════════════╝[/bold cyan]
"""

SAMPLE_QUERIES = [
    {
        "id": "1",
        "title": "Version Staleness & Ambiguity Test",
        "query": "What authentication mechanism does the payment gateway use?",
        "why": "Shows how RAG retrieves both legacy v1 (static API keys) and v2 (JWT), while OKF's frontmatter guarantees current production state.",
    },
    {
        "id": "2",
        "title": "Boundary Fragmentation Test",
        "query": "What are the prerequisite safety checks before running Step 4 in disaster recovery failover?",
        "why": "Shows how RAG slices critical runbook steps across chunk boundaries, while OKF preserves intact document structure.",
    },
    {
        "id": "3",
        "title": "Multi-Hop Relational Traversal Test",
        "query": "Which microservices depend on Vault Secrets Engine and must comply with PCI-DSS?",
        "why": "Shows how RAG fails multi-hop relation lookup, while OKF traverses explicit directed graph relations in YAML frontmatter.",
    },
    {
        "id": "4",
        "title": "Cardholder Governance & Scope Test",
        "query": "Which components are permitted inside the Cardholder Data Environment under PCI-DSS?",
        "why": "Shows exact compliance scope verification in OKF policy vs fragmented semantic matches in RAG.",
    },
]


def display_comparison(result: ComparisonResult):
    """Renders the detailed side-by-side comparison in the terminal."""
    console.print()
    console.print(Panel(f"[bold yellow]Query:[/bold yellow] [bold white]{result.query}[/bold white]", border_style="cyan"))

    # Table 1: Latency & Storage Overview
    summary_table = Table(title="[bold green]📊 Side-by-Side Pipeline Metrics[/bold green]", box=box.ROUNDED)
    summary_table.add_column("Dimension", style="bold cyan", width=22)
    summary_table.add_column("Classic Vector RAG", style="magenta", width=42)
    summary_table.add_column("Open Knowledge Format (OKF)", style="green", width=42)

    summary_table.add_row(
        "Storage Mechanism",
        result.rag.storage_type,
        result.okf.storage_type,
    )
    summary_table.add_row(
        "Storage Inspectability",
        "❌ Opaque (Dense floats, binary index)",
        "✅ 100% Human-Readable (Git & Markdown)",
    )
    summary_table.add_row(
        "Retrieval Method",
        result.rag.retrieval_method,
        result.okf.retrieval_method,
    )
    summary_table.add_row(
        "Retrieval Latency",
        f"[bold]{result.rag.latency_breakdown.get('total_retrieval_ms', 0)} ms[/bold] (Embed: {result.rag.latency_breakdown.get('embedding_latency_ms', 0)}ms, ANN: {result.rag.latency_breakdown.get('vector_search_latency_ms', 0)}ms)",
        f"[bold]{result.okf.latency_breakdown.get('index_and_traversal_ms', 0)} ms[/bold] (Instant Path/Graph Lookup)",
    )
    summary_table.add_row(
        "End-to-End Latency",
        f"[bold red]{result.rag.total_latency_ms} ms[/bold red]",
        f"[bold green]{result.okf.total_latency_ms} ms[/bold green] ({result.analysis['retrieval_speedup']})",
    )
    summary_table.add_row(
        "Boundary Integrity",
        result.rag.boundary_status,
        result.okf.boundary_status,
    )
    summary_table.add_row(
        "Audit Provenance",
        result.rag.provenance,
        result.okf.provenance,
    )
    summary_table.add_row(
        "Context Tokens",
        f"~{result.rag.token_count} tokens (stitched fragments)",
        f"~{result.okf.token_count} tokens (curated single document)",
    )

    console.print(summary_table)

    # Section 2: WHAT THEY STORE (Under the Hood Deep Dive)
    console.print()
    storage_table = Table(title="[bold yellow]🔍 Under the Hood: What Each System Actually Stores[/bold yellow]", box=box.HEAVY_EDGE)
    storage_table.add_column("Classic RAG Storage (Qdrant Point)", style="magenta", width=55)
    storage_table.add_column("OKF Storage (Filesystem / Git)", style="green", width=55)

    rag_chunks = result.rag.storage_payload_preview.get("stored_chunks_sample", [])
    rag_preview_text = f"Database: Qdrant Vector Engine\nVector Dim: {result.rag.storage_payload_preview.get('vector_dimension')} floats\n"
    if rag_chunks:
        rag_preview_text += f"\nPoint ID: {rag_chunks[0]['chunk_id']}\nCosine Score: {rag_chunks[0]['similarity_score']}\n"
        rag_preview_text += f"Vector Floats Sample:\n{rag_chunks[0]['vector_floats_sample']}...\n"
        rag_preview_text += f"\nRaw Chunk Payload:\n\"{rag_chunks[0]['chunk_id']}\": {result.rag.context_preview[:160]}..."
    else:
        rag_preview_text += f"Query Vector Sample:\n{result.rag.storage_payload_preview.get('query_vector_sample')}"

    okf_docs = result.okf.storage_payload_preview.get("documents_retrieved", [])
    okf_preview_text = "Filesystem: data/okf_bundle/\nFormat: Markdown + YAML Frontmatter\n"
    if okf_docs:
        d = okf_docs[0]
        okf_preview_text += f"\nDocument ID: {d['id']}\nVersion: {d['version']} (Status: {d['status']})\n"
        okf_preview_text += f"Verified By: {d['verified_by']}\n"
        okf_preview_text += f"Relations: {d['relations']}\n\nFrontmatter Header:\n---\n{d['frontmatter_raw']}\n---"
    else:
        okf_preview_text += "Master Index Manifest: data/okf_bundle/index.md"

    storage_table.add_row(rag_preview_text, okf_preview_text)
    console.print(storage_table)

    # Section 3: Generated Answers
    console.print()
    ans_table = Table(title="[bold cyan]💡 Generated Answers & Semantic Accuracy[/bold cyan]", box=box.SIMPLE_HEAVY)
    ans_table.add_column("Classic RAG Synthesized Answer", style="magenta", width=55)
    ans_table.add_column("OKF Synthesized Answer", style="green", width=55)
    ans_table.add_row(result.rag.answer, result.okf.answer)
    console.print(ans_table)

    # Section 4: Architectural Takeaway Box
    console.print()
    verdict = (
        f"[bold]🏆 Key Architectural Takeaways:[/bold]\n"
        f"• [bold green]Latency:[/bold green] {result.analysis['retrieval_speedup']}.\n"
        f"• [bold green]Storage Transparency:[/bold green] {result.analysis['storage_comparison']['okf']}\n"
        f"• [bold green]Hallucination Resistance:[/bold green] {result.analysis['hallucination_resistance']['okf']}\n"
        f"• [bold green]Relational Multi-Hop:[/bold green] {result.analysis['relational_reasoning']['okf']}"
    )
    console.print(Panel(verdict, title="[bold white]Architectural Verdict[/bold white]", border_style="green"))


def run_cli_interactive(comparator: BenchmarkComparator):
    """Interactive CLI menu loop."""
    console.clear()
    console.print(BANNER)

    while True:
        console.print()
        console.print("[bold cyan]Select a benchmark scenario or type a custom question:[/bold cyan]")
        for q in SAMPLE_QUERIES:
            console.print(f"  [bold yellow]{q['id']}[/bold yellow]. [bold white]{q['title']}[/bold white]")
            console.print(f"     [dim]Query:[/dim] \"{q['query']}\"")
            console.print(f"     [dim cyan]Purpose: {q['why']}[/dim cyan]")

        console.print("  [bold yellow]5[/bold yellow]. [bold green]Type your own custom question[/bold green]")
        console.print("  [bold yellow]q[/bold yellow]. [dim]Exit[/dim]")
        console.print()

        choice = Prompt.ask("[bold]Enter choice [1-5 or q][/bold]", default="1")
        if choice.lower() in ["q", "quit", "exit"]:
            console.print("\n[bold cyan]Thank you for exploring Open Knowledge Format vs RAG![/bold cyan]\n")
            break

        query = ""
        if choice in ["1", "2", "3", "4"]:
            idx = int(choice) - 1
            query = SAMPLE_QUERIES[idx]["query"]
        elif choice == "5":
            query = Prompt.ask("[bold yellow]Enter your question[/bold yellow]")
        else:
            console.print("[red]Invalid selection, please try again.[/red]")
            continue

        if not query.strip():
            continue

        with console.status(f"[bold cyan]Running RAG (Qdrant Vector DB) vs OKF (LLM-Wiki)...[/bold cyan]", spinner="dots"):
            result = comparator.compare(query.strip())

        display_comparison(result)

        Prompt.ask("\n[dim]Press [Enter] to continue back to the menu...[/dim]")
