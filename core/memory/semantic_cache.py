import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from config.settings import settings
from core.rag.embeddings import EmbeddingManager
from core.memory.vault_manager import ObsidianVaultManager

class SemanticPrecedentCache:
    """
    Caché Semántico de Consultas y Precedentes en el 'Cerebro Obsidiano'.
    Almacena las consultas exitosas verificadas en vault/consultas/ como notas Markdown
    con frontmatter YAML y vector de embedding.
    Permite recuperar respuestas completas en milisegundos sin re-computar la inferencia LLM.
    """

    def __init__(
        self,
        vault_manager: Optional[ObsidianVaultManager] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
        similarity_threshold: float = 0.78
    ):
        self.vault = vault_manager or ObsidianVaultManager()
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.threshold = similarity_threshold
        self.cache_dir = settings.VAULT_PATH / "consultas"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = settings.DATA_PATH / "consultas_index.json"
        self.entries: List[Dict[str, Any]] = []
        self._load_index()

    def _load_index(self):
        """Carga el índice de embeddings de consultas previas desde disco."""
        if self.index_file.exists():
            try:
                self.entries = json.loads(self.index_file.read_text(encoding="utf-8"))
            except Exception:
                self.entries = []
        else:
            self.entries = []

    def _save_index(self):
        """Persiste el índice de embeddings en disco."""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def check_precedent(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Evalúa si la consulta actual tiene un precedente semántico en la bóveda (similitud >= threshold).
        Combina similitud coseno vectorial de n-gramas con overlap léxico (Jaccard) excluyendo stopwords.
        Retorna la respuesta almacenada y metadatos, o None si es una consulta inédita.
        """
        if not self.entries:
            return None

        import re
        STOPWORDS = {"que", "qué", "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "a", "en", "para", "por", "si", "mi", "mis", "su", "sus", "sin", "con", "se", "del", "al"}
        words_q = set(re.findall(r'\w+', query.lower())) - STOPWORDS

        # Obtener embedding de la consulta entrante
        q_embeds = await self.embedding_manager.get_embeddings([query])
        if not q_embeds:
            return None
        q_vec = q_embeds[0]

        best_entry = None
        best_score = -1.0

        for entry in self.entries:
            cosine_score = self._cosine_similarity(q_vec, entry["embedding"])
            words_entry = set(re.findall(r'\w+', entry.get("query", "").lower())) - STOPWORDS
            union_len = len(words_q | words_entry)
            jaccard = (len(words_q & words_entry) / union_len) if union_len > 0 else 0.0

            if words_q == words_entry and words_q:
                score = 1.0
            else:
                score = 0.55 * cosine_score + 0.45 * jaccard

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score >= self.threshold:
            answer_content = best_entry.get("answer")
            if not answer_content:
                note = self.vault.get_note("consultas", best_entry["note_id"])
                answer_content = note.get("content", "") if note else ""
            return {
                "matched_query": best_entry["query"],
                "similarity": round(best_score, 3),
                "answer": answer_content,
                "sources": best_entry.get("sources", []),
                "grounding_status": best_entry.get("grounding_status", "✓ Precedente Verificado en Bóveda"),
                "note_id": best_entry["note_id"],
                "created_at": best_entry.get("created_at", "")
            }

        return None

    async def store_precedent(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        cartridge_name: str,
        grounding_status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Registra una consulta exitosa en la Bóveda de Obsidian y actualiza el índice semántico.
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        slug = "".join(c if c.isalnum() else "_" for c in query.lower()[:35]).strip("_")
        note_id = f"consulta_{timestamp}_{slug}"

        # 1. Extraer enlaces wiki [[...]] automáticos según las fuentes
        links = []
        for s in sources:
            src_name = s.get("source", "").replace(".md", "").replace(".txt", "")
            if src_name:
                links.append(f"[[{src_name}]]")

        meta = {
            "query": query,
            "cartridge": cartridge_name,
            "grounding_status": grounding_status,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            **(metadata or {})
        }

        # 2. Guardar nota en vault/consultas/
        path = self.vault.save_note(
            category="consultas",
            note_id=note_id,
            title=f"Consulta: {query[:60]}...",
            content=answer,
            metadata=meta,
            tags=["precedente", "consulta", cartridge_name],
            links=links
        )

        # 3. Calcular vector y agregar al índice
        embeds = await self.embedding_manager.get_embeddings([query])
        if embeds:
            self.entries.append({
                "note_id": note_id,
                "query": query,
                "embedding": embeds[0],
                "answer": answer,
                "sources": sources,
                "grounding_status": grounding_status,
                "created_at": meta["created_at"],
                "cartridge": cartridge_name
            })
            self._save_index()

        return path
