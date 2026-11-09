from typing import List, Dict, Any, Tuple
from core.rag.bm25_index import PureBM25Index
from core.rag.vector_store import LocalVectorStore

class HybridRetriever:
    """
    Recuperador Híbrido con Fusión de Rangos Recíprocos (Reciprocal Rank Fusion - RRF).
    Combina la precisión léxica literal de BM25 con la profundidad conceptual
    de la búsqueda vectorial densa.
    """

    def __init__(self, bm25_index: PureBM25Index, vector_store: LocalVectorStore, rrf_k: int = 60):
        self.bm25 = bm25_index
        self.vector_store = vector_store
        self.rrf_k = rrf_k

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # 1. Búsqueda Léxica
        bm25_results = self.bm25.search(query, top_k=top_k * 2)

        # 2. Búsqueda Semántica Densa
        vector_results = await self.vector_store.similarity_search(query, top_k=top_k * 2)

        # 3. Fusión RRF
        doc_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        # Ponderar BM25
        for rank, (doc, _) in enumerate(bm25_results):
            doc_id = doc.get("id", str(hash(doc.get("content", ""))))
            doc_map[doc_id] = doc
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # Ponderar Vectorial
        for rank, (doc, _) in enumerate(vector_results):
            doc_id = doc.get("id", str(hash(doc.get("content", ""))))
            doc_map[doc_id] = doc
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # Ordenar documentos por puntaje RRF combinado
        sorted_ids = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)

        final_results = []
        for doc_id in sorted_ids[:top_k]:
            doc = doc_map[doc_id]
            doc_copy = dict(doc)
            doc_copy["rrf_score"] = doc_scores[doc_id]
            final_results.append(doc_copy)

        return final_results
