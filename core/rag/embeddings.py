import os
import math
from typing import List, Optional
from config.settings import settings

class EmbeddingManager:
    """
    Gestor desacoplado de embeddings.
    Soporta generación vía Gemini Cloud o modelos locales.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or settings.LLM_PROVIDER).lower()

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.provider == "gemini":
            from google import genai
            from google.genai import types
            api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
            if api_key:
                client = genai.Client(api_key=api_key)
                response = await client.aio.models.embed_content(
                    model="text-embedding-004",
                    contents=texts
                )
                return [embedding.values for embedding in response.embeddings]

        # Fallback local determinista para entornos offline antes de instalar modelos pesados ONNX
        return [self._generate_fallback_embedding(t) for t in texts]

    def _generate_fallback_embedding(self, text: str, dim: int = 512) -> List[float]:
        """
        Generador de embedding sintético determinista para testing y offline bootstrap.
        Usa hashing criptográfico MD5 con n-gramas de caracteres y subpalabras.
        100% determinista y estable entre reinicios de procesos.
        """
        import hashlib
        import re

        vec = [0.0] * dim
        clean = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean.split()
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16) % dim
            weight = 2.0 / math.log(i + 2)
            vec[h] += weight

            # N-gramas de subpalabras (raíces léxicas)
            if len(word) >= 3:
                for n in range(3, min(6, len(word) + 1)):
                    for s in range(len(word) - n + 1):
                        sub_h = int(hashlib.md5(word[s:s+n].encode('utf-8')).hexdigest(), 16) % dim
                        vec[sub_h] += 0.5

        # Normalización L2
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec
