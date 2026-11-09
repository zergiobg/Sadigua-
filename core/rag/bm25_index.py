import math
import re
from typing import List, Dict, Any, Tuple

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

        scores = [0.0] * self.N

        for term in query_tokens:
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
