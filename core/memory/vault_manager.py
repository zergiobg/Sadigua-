import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import settings

class ObsidianVaultManager:
    """
    Gestor de la Memoria Persistente 'Cerebro Obsidiano'.
    Guarda y recupera notas, perfiles de expedientes y conceptos en formato
    Markdown estructurado con frontmatter YAML compatible 100% con Obsidian / Logseq.
    Totalmente auditable, legible e inspeccionable por humanos sin necesidad de software cerrado.
    """

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path or settings.VAULT_PATH
        self.categories = ["expedientes", "clientes", "conceptos", "jurisprudencia", "consultas"]
        self._initialize_structure()

    def _initialize_structure(self):
        self.vault_path.mkdir(parents=True, exist_ok=True)
        for cat in self.categories:
            (self.vault_path / cat).mkdir(parents=True, exist_ok=True)

    def _parse_frontmatter_and_content(self, text: str) -> tuple[Dict[str, Any], str]:
        """Extrae el frontmatter YAML y el cuerpo de una nota markdown sin dependencias externas."""
        metadata = {}
        content = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                yaml_block = parts[1].strip()
                content = parts[2].strip()
                for line in yaml_block.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if v.startswith("[") and v.endswith("]"):
                            # Lista simple
                            metadata[k] = [item.strip().strip('"').strip("'") for item in v[1:-1].split(",") if item.strip()]
                        else:
                            metadata[k] = v
        return metadata, content

    def save_note(
        self,
        category: str,
        note_id: str,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        links: Optional[List[str]] = None
    ) -> Path:
        """
        Crea o actualiza una nota markdown con frontmatter y enlaces [[wiki]].
        """
        target_dir = self.vault_path / category
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitizar nombre de archivo
        safe_filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', note_id) + ".md"
        filepath = target_dir / safe_filename

        meta = metadata or {}
        meta["id"] = note_id
        meta["titulo"] = title
        meta["actualizado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if tags:
            meta["tags"] = tags

        # Construir bloque YAML frontmatter
        yaml_lines = ["---"]
        for k, v in meta.items():
            if isinstance(v, list):
                items_str = ", ".join(f'"{x}"' for x in v)
                yaml_lines.append(f"{k}: [{items_str}]")
            else:
                yaml_lines.append(f'{k}: "{v}"')
        yaml_lines.append("---\n")

        # Construir cuerpo con enlaces Obsidian [[wiki]]
        body_lines = [f"# {title}\n"]
        body_lines.append(content.strip())
        
        if links:
            body_lines.append("\n\n## Enlaces Relacionados")
            for link in links:
                body_lines.append(f"- [[{link}]]")

        full_text = "\n".join(yaml_lines) + "\n".join(body_lines) + "\n"
        filepath.write_text(full_text, encoding="utf-8")
        return filepath

    def get_note(self, category: str, note_id: str) -> Optional[Dict[str, Any]]:
        safe_filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', note_id) + ".md"
        filepath = self.vault_path / category / safe_filename
        if not filepath.exists():
            return None

        text = filepath.read_text(encoding="utf-8")
        metadata, content = self._parse_frontmatter_and_content(text)
        return {
            "id": note_id,
            "category": category,
            "path": str(filepath),
            "metadata": metadata,
            "content": content
        }

    def list_notes(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        target_dirs = [self.vault_path / category] if category else [self.vault_path / c for c in self.categories]
        
        for d in target_dirs:
            if not d.exists():
                continue
            cat_name = d.name
            for file in d.glob("*.md"):
                text = file.read_text(encoding="utf-8")
                meta, content = self._parse_frontmatter_and_content(text)
                results.append({
                    "id": meta.get("id", file.stem),
                    "title": meta.get("titulo", file.stem),
                    "category": cat_name,
                    "filename": file.name,
                    "updated": meta.get("actualizado", ""),
                    "snippet": content[:200] + "..." if len(content) > 200 else content
                })
        return results

    def record_precedent_mutation(self, mutation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra la mutación en el Cerebro Obsidiano:
        1. Crea/actualiza la nota de la nueva jurisprudencia/norma con estado VIGENTE.
        2. Actualiza la nota del precedente anterior marcándolo como SUPERADO/DEROGADO.
        3. Inserta enlaces bidireccionales [[wiki]] para el Knowledge Graph de Obsidian.
        """
        source_doc = mutation.get("source_doc", "Norma_Nueva")
        target_norm = mutation.get("target_norm", "Norma_Anterior")
        mutation_type = mutation.get("mutation_type", "CAMBIO_DE_PRECEDENTE")
        regla_anterior = mutation.get("regla_anterior", "")
        regla_nueva = mutation.get("regla_nueva", "")
        autoridad = mutation.get("autoridad", "Corte Constitucional")
        fecha = mutation.get("fecha_mutacion", datetime.now().strftime("%Y-%m-%d"))

        source_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', source_doc.lower()).strip("_")
        target_slug = re.sub(r'[^a-zA-Z0-9_\-]', '_', target_norm.lower()).strip("_")

        # 1. Nota de la Norma Vigente (Sucesora)
        source_content = (
            f"## Regla de Decisión Vigente\n{regla_nueva}\n\n"
            f"### Trazabilidad de Mutación Jurídica\n"
            f"- **Tipo de Mutación:** {mutation_type}\n"
            f"- **Precedente / Norma Superada:** [[{target_slug}]]\n"
            f"- **Autoridad:** {autoridad}\n"
            f"- **Fecha:** {fecha}\n"
            f"- **Criterio Anterior que se recogió/modificó:**\n> «{regla_anterior}»\n"
        )
        source_meta = {
            "estado": "VIGENTE",
            "tipo": mutation_type,
            "autoridad": autoridad,
            "fecha": fecha,
            "supera_a": f"[[{target_slug}]]"
        }
        self.save_note(
            category="jurisprudencia",
            note_id=source_slug,
            title=f"Jurisprudencia Vigente: {source_doc}",
            content=source_content,
            metadata=source_meta,
            tags=["precedente", "vigente", "unificacion"],
            links=[target_slug]
        )

        # 2. Nota del Precedente Anterior (Marcado como SUPERADO)
        target_content = (
            f"> [!WARNING] PRECEDENTE SUPERADO O NORMA MODIFICADA\n"
            f"> Este criterio normativo/jurisprudencial fue expresamente superado o derogado por [[{source_slug}]].\n"
            f"> **Tipo:** {mutation_type} | **Fecha:** {fecha}\n\n"
            f"## Criterio Histórico Anterior\n{regla_anterior}\n\n"
            f"## Nueva Regla Vigente Adoptada\n{regla_nueva}\n"
        )
        target_meta = {
            "estado": "SUPERADO",
            "tipo": mutation_type,
            "autoridad": autoridad,
            "fecha_superacion": fecha,
            "superado_por": f"[[{source_slug}]]",
            "superceded_by": source_doc
        }
        self.save_note(
            category="jurisprudencia",
            note_id=target_slug,
            title=f"Precedente Histórico: {target_norm} (SUPERADO)",
            content=target_content,
            metadata=target_meta,
            tags=["precedente_historico", "superado", "archivo"],
            links=[source_slug]
        )

        return {
            "source_id": source_slug,
            "target_id": target_slug,
            "status": "synchronized_in_vault"
        }
