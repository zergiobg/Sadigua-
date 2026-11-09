import re
from typing import List, Dict, Any

SPANISH_STOPWORDS = {
    "para", "como", "cómo", "cual", "cuál", "cuales", "cuáles", "segun", "según",
    "sobre", "entre", "desde", "hasta", "donde", "dónde", "cuando", "cuándo",
    "quien", "quién", "quienes", "porque", "porqué", "esta", "está", "este",
    "estos", "estas", "esos", "esas", "aquel", "aquella", "tiene", "tienen",
    "puede", "pueden", "debe", "deben", "hacer", "hace", "ante", "bajo", "contra",
    "hacia", "mediante", "durante", "todo", "toda", "todos", "todas", "otro",
    "otra", "otros", "otras", "mismo", "misma", "caso", "casos", "forma", "manera"
}

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

        # Tokenización limpia sin signos de interrogación/puntuación ni stopwords genéricas
        raw_tokens = re.findall(r'\b[a-záéíóúñ0-9]+\b', query.lower())
        query_words = {
            w for w in raw_tokens
            if (len(w) > 3 or w.isdigit()) and w not in SPANISH_STOPWORDS
        }
        scored_candidates = []

        for doc in candidates:
            content = doc.get("content", "").lower()
            rrf_score = doc.get("rrf_score", 0.0)
            
            # Bonificación por coincidencia exacta de artículos y palabras clave sustantivas
            keyword_matches = sum(1 for w in query_words if w in content)
            final_score = rrf_score * (1.0 + 0.5 * keyword_matches)

            doc_with_score = dict(doc)
            doc_with_score["rerank_score"] = final_score
            scored_candidates.append(doc_with_score)

        # Ordenar por puntaje final
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_n]
