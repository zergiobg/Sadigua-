import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings

class CartridgeManager:
    """
    Gestor del Shell para 'Cartuchos de Dominio' en Sadigua.
    Permite descubrir, listar, inspeccionar y alternar entre bases de conocimiento
    especializadas (Derecho, CRM Telco, Medicina, etc.).
    """

    def __init__(self, cartridges_path: Optional[Path] = None):
        self.cartridges_path = cartridges_path or settings.CARTRIDGES_PATH
        self.cartridges_path.mkdir(parents=True, exist_ok=True)

    def _parse_yaml_simple(self, text: str) -> Dict[str, Any]:
        """Parser básico de YAML sin dependencias para leer manifest.yaml."""
        data = {}
        current_multiline_key = None
        multiline_buffer = []

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
                if current_multiline_key:
                    data[current_multiline_key] = " ".join(multiline_buffer).strip()
                    current_multiline_key = None
                    multiline_buffer = []

                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if v == ">" or v == "|":
                    current_multiline_key = k
                else:
                    data[k] = v
            elif current_multiline_key and (line.startswith("  ") or line.startswith("\t")):
                multiline_buffer.append(stripped)

        if current_multiline_key:
            data[current_multiline_key] = " ".join(multiline_buffer).strip()

        return data

    def list_cartridges(self) -> List[Dict[str, Any]]:
        cartridges = []
        if not self.cartridges_path.exists():
            return cartridges

        for folder in self.cartridges_path.iterdir():
            if folder.is_dir() and not folder.name.startswith("."):
                manifest_file = folder / "manifest.yaml"
                meta = {}
                if manifest_file.exists():
                    try:
                        meta = self._parse_yaml_simple(manifest_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass

                # Contar documentos en el corpus
                doc_count = 0
                corpus_dir = folder / "corpus"
                if corpus_dir.exists():
                    doc_count = len(list(corpus_dir.rglob("*.md"))) + \
                                len(list(corpus_dir.rglob("*.txt"))) + \
                                len(list(corpus_dir.rglob("*.pdf")))

                cartridges.append({
                    "id": folder.name,
                    "name": meta.get("display_name", folder.name),
                    "domain": meta.get("domain", "general"),
                    "version": meta.get("version", "1.0.0"),
                    "description": meta.get("description", "Cartucho de conocimiento Sadigua."),
                    "is_active": folder.name == settings.ACTIVE_CARTRIDGE,
                    "doc_count": doc_count
                })

        return cartridges

    def get_cartridge_documents(self, cartridge_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cid = cartridge_id or settings.ACTIVE_CARTRIDGE
        corpus_dir = self.cartridges_path / cid / "corpus"
        documents = []

        if not corpus_dir.exists():
            return documents

        for filepath in corpus_dir.rglob("*"):
            if filepath.is_file() and filepath.suffix.lower() in [".md", ".txt", ".pdf"]:
                stat = filepath.stat()
                documents.append({
                    "filename": filepath.name,
                    "relative_path": str(filepath.relative_to(corpus_dir)),
                    "extension": filepath.suffix.lower(),
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": stat.st_mtime
                })

        return sorted(documents, key=lambda x: x["filename"])

    def switch_cartridge(self, cartridge_id: str) -> bool:
        target_dir = self.cartridges_path / cartridge_id
        if not target_dir.exists() or not target_dir.is_dir():
            return False
        settings.ACTIVE_CARTRIDGE = cartridge_id
        return True
