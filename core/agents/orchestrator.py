from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from config.settings import settings
from core.engine.factory import get_llm_engine
from core.engine.base import BaseLLMEngine
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import PrecisionReranker
from core.memory.vault_manager import ObsidianVaultManager
from core.memory.conversation_buffer import ConversationBuffer
from core.agents.grounding_check import GroundingValidator

class SadiguaOrchestrator:
    """
    Orquestador Cognitivo Principal del Proyecto Sadigua.
    Gestiona el ciclo de vida de la consulta, la memoria 'Cerebro Obsidiano',
    el RAG híbrido normativo y la validación anti-alucinaciones.
    """

    def __init__(
        self,
        cartridge_name: Optional[str] = None,
        llm_engine: Optional[BaseLLMEngine] = None,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[PrecisionReranker] = None,
        vault_manager: Optional[ObsidianVaultManager] = None
    ):
        self.cartridge_name = cartridge_name or settings.ACTIVE_CARTRIDGE
        self.cartridge_path = settings.CARTRIDGES_PATH / self.cartridge_name
        self.llm = llm_engine or get_llm_engine()
        self.retriever = retriever
        self.reranker = reranker or PrecisionReranker()
        self.vault = vault_manager or ObsidianVaultManager()
        self.memory = ConversationBuffer()
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        prompt_file = self.cartridge_path / "system_prompt.txt"
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return (
            "Eres SADIGUA, un sistema de inteligencia artificial de alta precisión para gestión "
            "del conocimiento y análisis riguroso. Responde siempre con base en hechos verificables."
        )

    async def answer(self, user_query: str) -> Dict[str, Any]:
        """
        Flujo de razonamiento completo con recuperación, síntesis y validación fáctica.
        """
        self.memory.add_user_message(user_query)

        # 1. Recuperación Híbrida de Fragmentos Normativos
        retrieved_docs: List[Dict[str, Any]] = []
        if self.retriever:
            # Auto-ingesta si el índice está vacío
            if getattr(self.retriever.bm25, "N", 0) == 0:
                from core.rag.ingest import IngestionPipeline
                pipeline = IngestionPipeline(
                    cartridge_name=self.cartridge_name,
                    vector_store=self.retriever.vector_store,
                    bm25_index=self.retriever.bm25
                )
                await pipeline.ingest_corpus()

            candidates = await self.retriever.retrieve(user_query, top_k=6)
            retrieved_docs = self.reranker.rerank(user_query, candidates, top_n=3)

        # 2. Construcción del Prompt Enriquecido con Evidencias
        context_blocks = []
        for idx, doc in enumerate(retrieved_docs, start=1):
            source_label = doc.get("source", "Norma")
            section_label = doc.get("section", "")
            art_label = doc.get("articulo", "")
            header = f"[Fuente {idx}: {source_label} | {art_label or section_label}]"
            context_blocks.append(f"{header}\n{doc.get('content', '')}")

        context_str = "\n\n---\n\n".join(context_blocks)

        prompt = (
            f"CONSULTA DEL USUARIO / CASO JURÍDICO:\n{user_query}\n\n"
            f"FUENTES NORMATIVAS Y JURISPRUDENCIALES CURADAS DISPONIBLES:\n"
            f"{context_str if context_str else '[NO SE DISPONE DE FUENTES ESPECÍFICAS PARA ESTA CONSULTA]'}\n\n"
            "INSTRUCCIONES:\n"
            "Responde estrictamente con apego al contexto normativo disponible. "
            "Cita expresamente los artículos y normas que sustentan tu posición. "
            "Si las fuentes no contienen la respuesta, decláralo de manera explícita y no inventes normas."
        )

        # 3. Generación mediante Motor LLM Desacoplado
        raw_answer = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.1
        )

        # 4. Verificación de Grounding (Anti-Alucinaciones)
        is_grounded, grounding_msg, citations = GroundingValidator.validate(raw_answer, retrieved_docs)

        # 5. Persistencia en Memoria Corto Plazo
        self.memory.add_assistant_message(raw_answer, citations=citations)

        return {
            "answer": raw_answer,
            "grounded": is_grounded,
            "grounding_status": grounding_msg,
            "sources": [
                {
                    "source": d.get("source"),
                    "section": d.get("section"),
                    "articulo": d.get("articulo"),
                    "score": d.get("rerank_score", 0.0)
                }
                for d in retrieved_docs
            ],
            "citations_found": citations
        }
