from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

from config.settings import settings
from core.engine.factory import get_llm_engine
from core.engine.base import BaseLLMEngine
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import PrecisionReranker
from core.memory.vault_manager import ObsidianVaultManager
from core.memory.conversation_buffer import ConversationBuffer
from core.memory.semantic_cache import SemanticPrecedentCache
from core.agents.grounding_check import GroundingValidator

class SadiguaOrchestrator:
    """
    Orquestador Cognitivo Principal del Proyecto Sadigua.
    Gestiona el ciclo de vida de la consulta, la memoria 'Cerebro Obsidiano',
    el caché semántico de precedentes, el RAG híbrido normativo y la
    generación progresiva en ondas con telemetría.
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
        self.semantic_cache = SemanticPrecedentCache(vault_manager=self.vault)
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
        Flujo de razonamiento completo síncrono.
        1. Consulta Precedente Semántico en Bóveda (0.05s si existe).
        2. Si no existe, ejecuta RAG híbrido y generación LLM.
        3. Verifica Grounding y archiva el nuevo precedente en Bóveda.
        """
        self.memory.add_user_message(user_query)

        # 1. Chequeo de Caché Semántico en Bóveda
        cached = await self.semantic_cache.check_precedent(user_query)
        if cached:
            self.memory.add_assistant_message(cached["answer"], citations=[])
            return {
                "answer": cached["answer"],
                "grounded": True,
                "grounding_status": cached["grounding_status"] + f" (Similitud: {cached['similarity']*100:.0f}%)",
                "sources": cached["sources"],
                "citations_found": [],
                "precedent_hit": True,
                "matched_query": cached["matched_query"],
                "note_id": cached["note_id"]
            }

        # 2. Recuperación Híbrida de Fragmentos Normativos
        retrieved_docs: List[Dict[str, Any]] = []
        if self.retriever:
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

        # 3. Construcción del Prompt Enriquecido con Evidencias
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

        # 4. Generación mediante Motor LLM Desacoplado
        raw_answer = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.1
        )

        # 5. Verificación de Grounding (Anti-Alucinaciones)
        is_grounded, grounding_msg, citations = GroundingValidator.validate(raw_answer, retrieved_docs)

        # 6. Almacenamiento en Memoria y Caché de Precedentes en Bóveda
        self.memory.add_assistant_message(raw_answer, citations=citations)
        sources_meta = [
            {
                "source": d.get("source"),
                "section": d.get("section"),
                "articulo": d.get("articulo"),
                "score": float(d.get("rerank_score", 0.0))
            }
            for d in retrieved_docs
        ]
        note_path = await self.semantic_cache.store_precedent(
            query=user_query,
            answer=raw_answer,
            sources=sources_meta,
            cartridge_name=self.cartridge_name,
            grounding_status=grounding_msg
        )

        return {
            "answer": raw_answer,
            "grounded": is_grounded,
            "grounding_status": grounding_msg,
            "sources": sources_meta,
            "citations_found": citations,
            "precedent_hit": False,
            "note_id": note_path.stem
        }

    async def answer_progressive_stream(self, user_query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generador Asíncrono de Respuestas Progresivas en Ondas con Telemetría Activa.
        Yields eventos en tiempo real:
        - Estado de Fases (Búsqueda Precedentes -> RAG Híbrido -> Reranking)
        - Documentos consultados (para badges del HUD)
        - Onda 1: Dictamen y Fundamento Inmediato (Tokens en streaming)
        - Onda 2: Ruta Procesal, Tutela y Recursos (Tokens en streaming continuo)
        - Grounding final y Archivo de Precedente en Bóveda
        """
        # Fase 1: Caché Semántico de Precedentes
        yield {
            "type": "phase",
            "phase": "precedent_check",
            "message": "Consultando Bóveda de Precedentes en Memoria Obsidiana...",
            "progress": 10
        }

        cached = await self.semantic_cache.check_precedent(user_query)
        if cached:
            self.memory.add_user_message(user_query)
            self.memory.add_assistant_message(cached["answer"], citations=[])
            yield {
                "type": "precedent_hit",
                "matched_query": cached["matched_query"],
                "similarity": cached["similarity"],
                "answer": cached["answer"],
                "sources": cached["sources"],
                "grounding_status": f"✓ Precedente Verificado en Bóveda (Match {cached['similarity']*100:.0f}%)",
                "note_id": cached["note_id"],
                "progress": 100
            }
            yield {"type": "done", "note_id": cached["note_id"]}
            return

        # Fase 2: Recuperación RAG Híbrida
        yield {
            "type": "phase",
            "phase": "retrieval",
            "message": "Iniciando recuperación híbrida (BM25 Léxico + BGE-M3 Vectorial)...",
            "progress": 25
        }

        retrieved_docs: List[Dict[str, Any]] = []
        if self.retriever:
            if getattr(self.retriever.bm25, "N", 0) == 0:
                from core.rag.ingest import IngestionPipeline
                pipeline = IngestionPipeline(
                    cartridge_name=self.cartridge_name,
                    vector_store=self.retriever.vector_store,
                    bm25_index=self.retriever.bm25
                )
                await pipeline.ingest_corpus()

            candidates = await self.retriever.retrieve(user_query, top_k=6)
            yield {
                "type": "phase",
                "phase": "rerank",
                "message": f"Reranking neural de precisión sobre {len(candidates)} fragmentos normativos...",
                "progress": 40
            }
            retrieved_docs = self.reranker.rerank(user_query, candidates, top_n=3)

        # Emitir documentos encontrados para el HUD
        doc_badges = [
            {
                "source": d.get("source", "Norma"),
                "section": d.get("section", ""),
                "articulo": d.get("articulo", ""),
                "score": round(float(d.get("rerank_score", 0.0)), 3)
            }
            for d in retrieved_docs
        ]
        yield {
            "type": "documents_found",
            "documents": doc_badges,
            "progress": 50
        }

        # Construir contexto
        context_blocks = []
        for idx, doc in enumerate(retrieved_docs, start=1):
            source_label = doc.get("source", "Norma")
            section_label = doc.get("section", "")
            art_label = doc.get("articulo", "")
            header = f"[Fuente {idx}: {source_label} | {art_label or section_label}]"
            context_blocks.append(f"{header}\n{doc.get('content', '')}")
        context_str = "\n\n---\n\n".join(context_blocks)

        # Fase 3: Onda 1 (Dictamen y Fundamento Inmediato)
        yield {
            "type": "phase",
            "phase": "wave_1_start",
            "message": "Transmitiendo Onda 1: Dictamen y Fundamento Jurídico Inmediato...",
            "wave": 1,
            "progress": 60
        }

        prompt_wave_1 = (
            f"CONSULTA DEL USUARIO / CASO JURÍDICO:\n{user_query}\n\n"
            f"FUENTES NORMATIVAS Y JURISPRUDENCIALES CURADAS DISPONIBLES:\n"
            f"{context_str if context_str else '[NO SE DISPONE DE FUENTES ESPECÍFICAS PARA ESTA CONSULTA]'}\n\n"
            "INSTRUCCIÓN PARA LA ONDA 1 (DICTAMEN Y FUNDAMENTOS INMEDIATOS):\n"
            "Responde de forma directa, rigurosa y concisa estructurando:\n"
            "1. Veredicto jurídico directo sobre el caso.\n"
            "2. Fundamento normativo aplicable con cita textual de artículos y normas del contexto.\n"
            "3. Breve análisis y subsunción jurídica del caso.\n"
            "NO incluyas aún la ruta procesal o memoriales detallados (se generarán en la siguiente sección)."
        )

        wave_1_text = ""
        try:
            async for token in self.llm.stream(
                prompt=prompt_wave_1,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=450
            ):
                wave_1_text += token
                yield {"type": "token", "wave": 1, "text": token}
        except Exception as e:
            # Fallback en caso de error en streaming
            wave_1_text = await self.llm.generate(prompt=prompt_wave_1, system_prompt=self.system_prompt)
            yield {"type": "token", "wave": 1, "text": wave_1_text}

        yield {
            "type": "phase",
            "phase": "wave_1_done",
            "message": "Onda 1 entregada. Cocinando Onda 2: Ruta Procesal, Tutela y Recursos...",
            "wave": 1,
            "progress": 75
        }

        # Fase 4: Onda 2 (Ruta Procesal, Tutela y Recursos)
        yield {
            "type": "phase",
            "phase": "wave_2_start",
            "message": "Transmitiendo Onda 2: Procedimiento Procesal y Acciones Concretas...",
            "wave": 2,
            "progress": 80
        }

        prompt_wave_2 = (
            f"CONSULTA ORIGINAL:\n{user_query}\n\n"
            f"DICTAMEN JURÍDICO Y FUNDAMENTOS YA EMITIDOS EN ONDA 1:\n{wave_1_text}\n\n"
            f"FUENTES NORMATIVAS:\n{context_str}\n\n"
            "INSTRUCCIÓN PARA LA ONDA 2 (RUTA PROCESAL, ACCIONES PRÁCTICAS Y TUTELA):\n"
            "Con base en el dictamen ya emitido, detalla ahora de manera exhaustiva y práctica:\n"
            "1. Ruta procesal paso a paso para el afectado.\n"
            "2. Acciones concretas: Reclamación directa, Derecho de Petición, Denuncia ante SIC / Entidad competente o Acción de Tutela.\n"
            "3. Recomendación práctica final y medidas cautelares o preventivas.\n"
            "Redacta con precisión jurídica y claridad práctica."
        )

        wave_2_text = ""
        try:
            async for token in self.llm.stream(
                prompt=prompt_wave_2,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=800
            ):
                wave_2_text += token
                yield {"type": "token", "wave": 2, "text": token}
        except Exception as e:
            wave_2_text = await self.llm.generate(prompt=prompt_wave_2, system_prompt=self.system_prompt)
            yield {"type": "token", "wave": 2, "text": wave_2_text}

        yield {
            "type": "phase",
            "phase": "wave_2_done",
            "message": "Onda 2 completada.",
            "wave": 2,
            "progress": 95
        }

        # Fase 5: Grounding, Guardado en Bóveda Obsidiana y Finalización
        full_answer = f"{wave_1_text.strip()}\n\n---\n\n{wave_2_text.strip()}"
        is_grounded, grounding_msg, citations = GroundingValidator.validate(full_answer, retrieved_docs)

        sources_meta = [
            {
                "source": d.get("source"),
                "section": d.get("section"),
                "articulo": d.get("articulo"),
                "score": float(d.get("rerank_score", 0.0))
            }
            for d in retrieved_docs
        ]

        note_path = await self.semantic_cache.store_precedent(
            query=user_query,
            answer=full_answer,
            sources=sources_meta,
            cartridge_name=self.cartridge_name,
            grounding_status=grounding_msg
        )

        self.memory.add_user_message(user_query)
        self.memory.add_assistant_message(full_answer, citations=citations)

        yield {
            "type": "grounding",
            "grounded": is_grounded,
            "grounding_status": grounding_msg,
            "citations": citations,
            "note_id": note_path.stem,
            "sources": sources_meta,
            "progress": 100
        }

        yield {"type": "done", "note_id": note_path.stem}
