from pathlib import Path
from typing import List
from pydantic import BaseModel


class TextChunk(BaseModel):
    chunk_id: str
    source_file: str
    chunk_index: int
    text: str
    char_start: int
    char_end: int
    is_boundary_cut: bool = False


def chunk_text(text: str, source_file: str, chunk_size: int = 360, overlap: int = 60) -> List[TextChunk]:
    """Slices unstructured text into fixed-size chunks with overlapping boundaries,

    mimicking standard production vector RAG ingestion.
    """
    chunks: List[TextChunk] = []
    text_len = len(text)
    start = 0
    idx = 0

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_str = text[start:end]

        # Detect boundary fragmentation: does chunk cut mid-sentence?
        is_boundary_cut = False
        if end < text_len:
            # If the next character is not a newline or space, or chunk ends mid-word
            if not text[end - 1] in [".", "\n", "!", "?"]:
                is_boundary_cut = True

        chunks.append(
            TextChunk(
                chunk_id=f"{Path(source_file).stem}_chunk_{idx}",
                source_file=source_file,
                chunk_index=idx,
                text=chunk_str,
                char_start=start,
                char_end=end,
                is_boundary_cut=is_boundary_cut,
            )
        )
        idx += 1
        if end == text_len:
            break
        start += (chunk_size - overlap)

    return chunks


def chunk_documents_in_dir(raw_dir: Path, chunk_size: int = 360, overlap: int = 60) -> List[TextChunk]:
    """Chunks all text files in raw documents directory."""
    all_chunks: List[TextChunk] = []
    for txt_file in sorted(raw_dir.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8")
        file_chunks = chunk_text(content, txt_file.name, chunk_size=chunk_size, overlap=overlap)
        all_chunks.extend(file_chunks)
    return all_chunks
