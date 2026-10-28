import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from pydantic import BaseModel, Field, ConfigDict


class OKFDocument(BaseModel):
    """Represents a validated Open Knowledge Format (OKF) document."""
    file_path: str
    rel_path: str
    doc_type: str = Field(default="document", alias="type")
    id: str
    title: str
    version: str = "1.0.0"
    status: str = "active"
    updated_at: Optional[str] = None
    verified_by: Optional[str] = None
    resource: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    relations: Dict[str, Any] = Field(default_factory=dict)
    frontmatter_raw: str = ""
    body_markdown: str = ""
    full_content: str = ""

    model_config = ConfigDict(populate_by_name=True)


FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_okf_file(file_path: Path, base_dir: Optional[Path] = None) -> OKFDocument:
    """Parses a Markdown file with YAML frontmatter conforming to OKF specifications."""
    content = file_path.read_text(encoding="utf-8")
    rel_path = str(file_path.relative_to(base_dir)) if base_dir else str(file_path)

    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        # Fallback if no frontmatter is found
        filename_id = file_path.stem
        return OKFDocument(
            file_path=str(file_path),
            rel_path=rel_path,
            doc_type="unclassified",
            id=filename_id,
            title=filename_id.replace("-", " ").title(),
            frontmatter_raw="",
            body_markdown=content.strip(),
            full_content=content,
        )

    fm_raw = match.group(1)
    body = match.group(2).strip()

    try:
        metadata = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as e:
        metadata = {"error": f"Invalid YAML frontmatter: {e}"}

    doc_id = str(metadata.get("id") or metadata.get("bundle_name") or file_path.stem)
    doc_type = str(metadata.get("type", "document"))
    title = str(metadata.get("title") or metadata.get("bundle_name") or doc_id.replace("-", " ").title())
    version = str(metadata.get("version", "1.0.0"))
    status = str(metadata.get("status", "active"))
    updated_at = str(metadata.get("updated_at", ""))
    verified_by = metadata.get("verified_by")
    resource = metadata.get("resource")
    tags = metadata.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    relations = metadata.get("relations") or {}

    return OKFDocument(
        file_path=str(file_path),
        rel_path=rel_path,
        doc_type=doc_type,
        id=doc_id,
        title=title,
        version=version,
        status=status,
        updated_at=updated_at,
        verified_by=verified_by,
        resource=resource,
        tags=tags,
        relations=relations,
        frontmatter_raw=fm_raw.strip(),
        body_markdown=body,
        full_content=content,
    )
