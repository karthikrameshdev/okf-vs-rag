from pathlib import Path
from typing import Dict, List, Optional, Any
from .parser import OKFDocument, parse_okf_file


class OKFBundleIndex:
    """Manages the structured Open Knowledge Format bundle, entity registry, and relationship graph."""

    def __init__(self, bundle_dir: Path):
        self.bundle_dir = bundle_dir
        self.manifest: Optional[OKFDocument] = None
        self.docs_by_id: Dict[str, OKFDocument] = {}
        self.docs_by_path: Dict[str, OKFDocument] = {}
        self.docs_by_type: Dict[str, List[OKFDocument]] = {}
        self.tag_index: Dict[str, List[str]] = {}
        self.relations_graph: Dict[str, Dict[str, List[str]]] = {}
        self.load_bundle()

    def load_bundle(self):
        """Scans and indexes the OKF bundle."""
        self.docs_by_id.clear()
        self.docs_by_path.clear()
        self.docs_by_type.clear()
        self.tag_index.clear()
        self.relations_graph.clear()

        manifest_path = self.bundle_dir / "index.md"
        if manifest_path.exists():
            self.manifest = parse_okf_file(manifest_path, self.bundle_dir)

        # Index all markdown files
        for md_file in sorted(self.bundle_dir.rglob("*.md")):
            doc = parse_okf_file(md_file, self.bundle_dir)
            self.docs_by_id[doc.id] = doc
            self.docs_by_path[doc.rel_path] = doc

            # Group by type
            if doc.doc_type not in self.docs_by_type:
                self.docs_by_type[doc.doc_type] = []
            self.docs_by_type[doc.doc_type].append(doc)

            # Index tags
            for tag in doc.tags:
                tag_lower = tag.lower()
                if tag_lower not in self.tag_index:
                    self.tag_index[tag_lower] = []
                self.tag_index[tag_lower].append(doc.id)

            # Build graph relations
            if doc.relations:
                self.relations_graph[doc.id] = {}
                for rel_key, rel_val in doc.relations.items():
                    if isinstance(rel_val, list):
                        self.relations_graph[doc.id][rel_key] = [str(v) for v in rel_val]
                    else:
                        self.relations_graph[doc.id][rel_key] = [str(rel_val)]

    def get_document(self, doc_id: str) -> Optional[OKFDocument]:
        return self.docs_by_id.get(doc_id)

    def get_all_documents(self) -> List[OKFDocument]:
        return list(self.docs_by_id.values())

    def get_related_entities(self, doc_id: str, relation_type: Optional[str] = None) -> List[str]:
        """Finds related entities for an entity ID, traversing directed relations."""
        rel_map = self.relations_graph.get(doc_id, {})
        if relation_type:
            return rel_map.get(relation_type, [])
        all_related = []
        for targets in rel_map.values():
            all_related.extend(targets)
        return list(set(all_related))

    def find_dependents(self, target_id: str) -> List[str]:
        """Reverse lookup: Find all entities that depend on, or are governed by, target_id."""
        dependents = []
        for source_id, rels in self.relations_graph.items():
            for rel_type, targets in rels.items():
                if target_id in targets:
                    dependents.append(source_id)
        return list(set(dependents))

    def get_bundle_tree(self) -> Dict[str, Any]:
        """Generates a hierarchical tree representation of the OKF bundle files."""
        tree = {"name": self.bundle_dir.name, "type": "directory", "children": []}
        
        def insert_into_tree(root_dict, parts, doc):
            if len(parts) == 1:
                root_dict["children"].append({
                    "name": parts[0],
                    "type": "file",
                    "id": doc.id,
                    "title": doc.title,
                    "doc_type": doc.doc_type,
                    "status": doc.status,
                    "version": doc.version,
                    "rel_path": doc.rel_path,
                })
                return

            current_dir_name = parts[0]
            for child in root_dict["children"]:
                if child.get("type") == "directory" and child.get("name") == current_dir_name:
                    insert_into_tree(child, parts[1:], doc)
                    return

            new_dir = {"name": current_dir_name, "type": "directory", "children": []}
            root_dict["children"].append(new_dir)
            insert_into_tree(new_dir, parts[1:], doc)

        for doc in self.docs_by_id.values():
            parts = Path(doc.rel_path).parts
            insert_into_tree(tree, parts, doc)

        return tree
