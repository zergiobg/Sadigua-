import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from core.rag.embeddings import EmbeddingManager
from config.settings import settings

class LocalVectorStore:
    """
    Base de datos vectorial local autónoma.
    Almacena embeddings y metadatos con persistencia JSON/SQLite y búsqueda por similitud de coseno.
    No requiere servidores externos obligatorios para operar de forma soberana.
    """

    def __init__(self, storage_path: Optional[Path] = None, embedding_manager: Optional[EmbeddingManager] = None):
        self.storage_path = storage_path or (settings.DATA_PATH / "vectors.json")
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self.documents = data.get("documents", [])
                self.embeddings = data.get("embeddings", [])
            except Exception:
                self.documents = []
                self.embeddings = []

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings
        }
        self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    async def add_documents(self, docs: List[Dict[str, Any]]):
        if not docs:
            return
        texts = [d.get("content", "") for d in docs]
        new_embeddings = await self.embedding_manager.get_embeddings(texts)
        
        self.documents.extend(docs)
        self.embeddings.extend(new_embeddings)
        self._save()

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def similarity_search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not self.documents or not self.embeddings:
            return []

        query_embeds = await self.embedding_manager.get_embeddings([query])
        query_vec = query_embeds[0]

        scores = []
        for idx, doc_vec in enumerate(self.embeddings):
            sim = self._cosine_similarity(query_vec, doc_vec)
            scores.append((self.documents[idx], sim))

        # Ordenar por similitud descendente
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
