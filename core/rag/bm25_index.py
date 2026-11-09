import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from config.settings import settings

LEGAL_QUERY_STOPWORDS = {
    "que", "qué", "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "a", "en", "para", "por", "si", "mi", "mis", "su", "sus", "sin",
    "con", "se", "del", "al", "es", "son", "como", "sobre", "mas", "más", "pero",
    "articulo", "artículo", "art", "arts", "ley", "norma", "normas", "codigo", "código",
    "constitucion", "constitución", "cosntitucion", "cosntitución", "colombia", "colombiana",
    "habla", "dice", "trata", "menciona", "refiere", "establece", "dispone", "consagra",
    "cual", "cuál", "cuales", "cuáles", "donde", "dónde", "cuando", "cuándo"
}

class PureBM25Index:
    """
    Motor de Búsqueda Léxica BM25 (Okapi) de alta precisión.
    Diseñado para encontrar términos normativos literales, artículos de ley,
    números de decretos o referencias procesales exactas.
    Totalmente autónomo y sin dependencias C++ pesadas.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.N: int = 0

    def save(self, filepath: Optional[Path] = None):
        """Persiste el índice BM25 serializado a disco en JSON."""
        import json
        p = filepath or (settings.DATA_PATH / "bm25.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "corpus": self.corpus,
            "N": self.N,
            "avg_doc_len": self.avg_doc_len,
            "doc_lengths": self.doc_lengths,
            "idf": self.idf,
            "doc_freqs": self.doc_freqs,
            "tokenized_corpus": self.tokenized_corpus
        }
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def load(self, filepath: Optional[Path] = None) -> bool:
        """Carga el índice BM25 persistido desde disco."""
        import json
        p = filepath or (settings.DATA_PATH / "bm25.json")
        if not p.exists():
            return False
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            self.corpus = data.get("corpus", [])
            self.N = data.get("N", 0)
            self.avg_doc_len = data.get("avg_doc_len", 0.0)
            self.doc_lengths = data.get("doc_lengths", [])
            self.idf = data.get("idf", {})
            self.doc_freqs = data.get("doc_freqs", {})
            self.tokenized_corpus = data.get("tokenized_corpus", [])
            return self.N > 0
        except Exception:
            return False

    def _tokenize(self, text: str) -> List[str]:
        # Tokenización para español: minúsculas, palabras y números
        tokens = re.findall(r'\b[a-záéíóúñ0-9_]+\b', text.lower())
        return tokens

    def index(self, documents: List[Dict[str, Any]]):
        self.corpus = documents
        self.tokenized_corpus = [self._tokenize(doc.get("content", "")) for doc in documents]
        self.N = len(documents)
        if self.N == 0:
            return

        self.doc_lengths = [len(doc) for doc in self.tokenized_corpus]
        self.avg_doc_len = sum(self.doc_lengths) / self.N

        self.doc_freqs = {}
        for doc in self.tokenized_corpus:
            seen_terms = set(doc)
            for term in seen_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Calcular IDF
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # BM25 IDF con suavizado
            self.idf[term] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.N == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Filtrar stopwords para no contaminar la búsqueda con palabras ultra-comunes
        substantive_tokens = [t for t in query_tokens if t not in LEGAL_QUERY_STOPWORDS]
        tokens_to_search = substantive_tokens if substantive_tokens else query_tokens

        scores = [0.0] * self.N

        for term in tokens_to_search:
            if term not in self.idf:
                continue
            term_idf = self.idf[term]

            for doc_idx, doc_tokens in enumerate(self.tokenized_corpus):
                term_count = doc_tokens.count(term)
                if term_count == 0:
                    continue

                doc_len = self.doc_lengths[doc_idx]
                numerator = term_count * (self.k1 + 1)
                denominator = term_count + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                scores[doc_idx] += term_idf * (numerator / denominator)

        # Ordenar por puntaje descendente
        ranked_indices = sorted(range(self.N), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked_indices[:top_k]:
            if scores[i] > 0.0:
                results.append((self.corpus[i], float(scores[i])))

        return results
