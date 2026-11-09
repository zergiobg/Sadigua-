from typing import List, Dict, Any

class PrecisionReranker:
    """
    Reranker de Alta Precisión.
    Reordena los candidatos recuperados y descarta fragmentos de bajo valor probatorio
    para evitar saturar la ventana de contexto del LLM con ruido.
    """

    def __init__(self, min_threshold: float = 0.01):
        self.min_threshold = min_threshold

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        # Heurística de precisión de términos de coincidencia en consultas normativas
        query_words = set(query.lower().split())
        scored_candidates = []

        for doc in candidates:
            content = doc.get("content", "").lower()
            rrf_score = doc.get("rrf_score", 0.0)
            
            # Bonificación por coincidencia exacta de artículos y palabras clave
            keyword_matches = sum(1 for w in query_words if len(w) > 3 and w in content)
            final_score = rrf_score * (1.0 + 0.5 * keyword_matches)

            doc_with_score = dict(doc)
            doc_with_score["rerank_score"] = final_score
            scored_candidates.append(doc_with_score)

        # Ordenar por puntaje final
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_n]
