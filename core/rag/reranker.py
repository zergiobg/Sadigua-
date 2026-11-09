import re
from typing import List, Dict, Any

SPANISH_STOPWORDS = {
    "para", "como", "cómo", "cual", "cuál", "cuales", "cuáles", "segun", "según",
    "sobre", "entre", "desde", "hasta", "donde", "dónde", "cuando", "cuándo",
    "quien", "quién", "quienes", "porque", "porqué", "esta", "está", "este",
    "estos", "estas", "esos", "esas", "aquel", "aquella", "tiene", "tienen",
    "puede", "pueden", "debe", "deben", "hacer", "hace", "ante", "bajo", "contra",
    "hacia", "mediante", "durante", "todo", "toda", "todos", "todas", "otro",
    "otra", "otros", "otras", "mismo", "misma", "caso", "casos", "forma", "manera",
    "articulo", "artículo", "art", "arts", "constitucion", "constitución", "cosntitucion",
    "cosntitución", "colombia", "colombiana", "habla", "dice", "trata", "menciona",
    "refiere", "establece", "dispone", "consagra"
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

        # Detección de consulta de antecedentes o historia de la norma
        is_historical_query = any(hw in query.lower() for hw in ["antes", "anterior", "historico", "histórico", "derogad", "superad", "evolucion", "evolución", "pasado", "antigua"])

        for doc in candidates:
            content = doc.get("content", "").lower()
            rrf_score = doc.get("rrf_score") or doc.get("score") or doc.get("lexical_score") or 1.0
            
            # Bonificación por coincidencia exacta de artículos y palabras clave sustantivas
            keyword_matches = sum(1 for w in query_words if w in content)
            has_article_label = bool(doc.get("articulo"))
            
            # Factor de bonificación: cada palabra sustantiva multiplica el score
            multiplier = 1.0 + (3.0 * keyword_matches)
            if has_article_label and keyword_matches > 0:
                multiplier *= 1.5

            # Ponderación de Vigencia: si está superado y la consulta NO es histórica, penalizar
            if doc.get("vigencia_status") == "SUPERADO":
                if not is_historical_query:
                    multiplier *= 0.20  # Prevalece la norma vigente
                else:
                    multiplier *= 1.80  # Bonifica en consultas históricas

            final_score = rrf_score * multiplier

            doc_with_score = dict(doc)
            doc_with_score["rerank_score"] = final_score
            scored_candidates.append(doc_with_score)

        # Ordenar por puntaje final
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored_candidates[:top_n]
