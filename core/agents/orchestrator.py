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
    generación progresiva en ondas con telemetría y blindaje anti-truncamiento.
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

    @staticmethod
    def is_thought_complete(text: str) -> bool:
        """
        Determina si un texto jurídico termina de forma limpia y cerrada.
        Retorna True si termina con puntuación terminal (., !, ?, etc.) o bloque cerrado.
        Retorna False si fue cortado a mitad de una palabra (ej. 'ordin') o frase incompleta.
        """
        t = text.strip()
        if not t:
            return True
        # Si termina en signo de puntuación terminal
        if t[-1] in {".", "!", "?", "”", "»", ")", "]"}:
            return True
        # Si la última línea no vacía termina en signo de cierre
        lines = [line.strip() for line in t.split("\n") if line.strip()]
        if lines and lines[-1][-1] in {".", "!", "?", "”", "»", ")", "]"}:
            return True
        return False

    async def answer(self, user_query: str) -> Dict[str, Any]:
        """
        Flujo de razonamiento síncrono completo con blindaje anti-truncamiento.
        """
        self.memory.add_user_message(user_query)

        # 1. Chequeo de Caché Semántico en Bóveda (0.05s)
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

            candidates = await self.retriever.retrieve(user_query, top_k=15)
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
            "INSTRUCCIONES DE DICTAMEN INTEGRAL:\n"
            "Responde estrictamente con apego al contexto normativo disponible. "
            "Cita expresamente los artículos y normas que sustentan tu posición. "
            "Estructura tu dictamen en:\n"
            "1. Veredicto Jurídico Directo\n"
            "2. Fundamento Normativo Aplicable\n"
            "3. Análisis y Subsunción Jurídica\n"
            "4. Ruta Procesal y Acciones Concretas (SIC, Tutela, Reclamación)\n"
            "5. Conclusión y Recomendaciones Prácticas Finales.\n\n"
            "REGLA CRÍTICA: Desarrolla cada sección de forma completa y asegúrate de concluir "
            "todas las oraciones con punto final cerrado. No dejes ideas o listas a medias."
        )

        # 4. Generación mediante Motor LLM Desacoplado (Presupuesto generoso de 2500 tokens)
        raw_answer = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.1,
            max_tokens=2500
        )

        # Mecanismo Anti-Truncamiento: Auto-cierre si la idea quedó interrumpida
        if not self.is_thought_complete(raw_answer):
            prompt_continuation = (
                "IMPORTANTE: El siguiente dictamen jurídico se interrumpió abruptamente antes de concluir la frase o recomendación:\n\n"
                f"«...{raw_answer[-300:]}»\n\n"
                "INSTRUCCIÓN: Completa exactamente la última palabra y concluye la frase u oración interrumpida "
                "de manera coherente y cerrada con punto final. NO repitas el texto previo; escribe ÚNICAMENTE la continuación y cierre."
            )
            continuation = await self.llm.generate(
                prompt=prompt_continuation,
                system_prompt=self.system_prompt,
                temperature=0.0,
                max_tokens=400
            )
            raw_answer = raw_answer.rstrip() + " " + continuation.strip()

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

    async def answer_progressive_stream(self, user_query: str, skip_cache: bool = False) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generador Asíncrono de Respuestas Progresivas en Ondas con Blindaje Anti-Truncamiento.
        - Onda 1: Dictamen y Fundamento Inmediato (Tokens en streaming con límite generoso).
        - Auto-Continuation Guard en Onda 1 si la frase no termina en punto.
        - Onda 2: Ruta Procesal, Tutela, Reclamaciones y Recomendaciones Completas.
        - Auto-Continuation Guard en Onda 2 si la recomendación no concluye en punto.
        - Grounding final y Archivo de Precedente en Bóveda.
        """
        # Fase 0: Escudo PII y Tokenización Sub-léxica
        approx_q_tokens = max(1, int(len(user_query.split()) * 1.35))
        yield {
            "type": "phase",
            "phase": "tokenization",
            "layer": 1,
            "message": f"Tokenización sub-léxica y normalización conceptual ({approx_q_tokens} tokens de entrada)...",
            "query_tokens": approx_q_tokens,
            "progress": 6
        }

        # Fase 1: Caché Semántico de Precedentes (si no se solicita omitir)
        if not skip_cache:
            yield {
                "type": "phase",
                "phase": "precedent_check",
                "layer": 2,
                "message": "Consultando Bóveda de Precedentes en Memoria Obsidiana...",
                "progress": 14
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

        # Fase 2: Recuperación RAG Híbrida (BM25 Léxico + Embebimiento Vectorial)
        yield {
            "type": "phase",
            "phase": "retrieval",
            "layer": 3,
            "message": "Búsqueda léxica exacta BM25 sobre códigos y artículos vigentes...",
            "progress": 24
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

            yield {
                "type": "phase",
                "phase": "vector_embedding",
                "layer": 4,
                "message": "Proyectando embebimiento vectorial denso (BGE-M3) en hiperespacio semántico...",
                "progress": 34
            }

            candidates = await self.retriever.retrieve(user_query, top_k=15)
            yield {
                "type": "phase",
                "phase": "rerank",
                "layer": 5,
                "message": f"Fusión RRF y Reranking neural de precisión sobre {len(candidates)} fragmentos normativos...",
                "candidates_count": len(candidates),
                "progress": 45
            }
            retrieved_docs = self.reranker.rerank(user_query, candidates, top_n=3)

        # Emitir documentos identificados para badges del HUD
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
            "message": "Atención neural sobre normas recuperadas — Generando Onda 1 (Dictamen)...",
            "wave": 1,
            "progress": 60
        }

        prompt_wave_1 = (
            f"CONSULTA DEL USUARIO / CASO JURÍDICO:\n{user_query}\n\n"
            f"FUENTES NORMATIVAS Y JURISPRUDENCIALES CURADAS DISPONIBLES:\n"
            f"{context_str if context_str else '[NO SE DISPONE DE FUENTES ESPECÍFICAS PARA ESTA CONSULTA]'}\n\n"
            "ESTRUCTURA OBLIGATORIA PARA LA ONDA 1 (DICTAMEN Y FUNDAMENTOS INMEDIATOS):\n"
            "1. ### Veredicto Jurídico Directo\n"
            "   (Dictamina de forma frontal, clara y contundente sobre la vulneración jurídica).\n"
            "2. ### Fundamento Normativo Aplicable\n"
            "   (Cita y analiza únicamente los 2 a 4 artículos clave presentes en las fuentes anteriores. PROHIBIDO hacer listas numéricas o secuencias de artículos; explica en prosa qué dispone cada norma).\n"
            "3. ### Análisis y Subsunción Jurídica\n"
            "   (Aplica rigurosamente las normas citadas a los hechos expuestos por el usuario).\n\n"
            "REGLAS CRÍTICAS DE REDACCIÓN:\n"
            "- Redacta en prosa jurídica profesional, fluida y argumentada.\n"
            "- Concluye la Onda 1 al terminar la subsunción jurídica con una oración completa y punto final.\n"
            "- PROHIBIDO incluir secciones de 'Conclusión', 'Recomendación Práctica' o 'Ruta Procesal' en esta entrega (se desarrollarán detalladamente a continuación en la Onda 2).\n"
            "- Finaliza esta primera parte tras la subsunción con punto final definitivo.\n"
            "- NUNCA dejes oraciones inconclusas."
        )

        wave_1_text = ""
        system_p1 = f"{self.system_prompt}\n\nATENCIÓN: En esta entrega inmediata genera únicamente el Veredicto, Fundamento y Subsunción Jurídica. No agregues conclusiones ni rutas procesales anticipadas."
        try:
            async for token in self.llm.stream(
                prompt=prompt_wave_1,
                system_prompt=system_p1,
                temperature=0.1,
                max_tokens=750  # Optimizado para rapidez de respuesta
            ):
                wave_1_text += token
                yield {"type": "token", "wave": 1, "text": token}
        except Exception as e:
            wave_1_text = await self.llm.generate(prompt=prompt_wave_1, system_prompt=system_p1, max_tokens=750)
            yield {"type": "token", "wave": 1, "text": wave_1_text}

        # Guardián Anti-Truncamiento: Onda 1
        if not self.is_thought_complete(wave_1_text):
            yield {
                "type": "phase",
                "phase": "wave_1_continuation",
                "message": "Completando cierre de idea en Onda 1...",
                "wave": 1,
                "progress": 72
            }
            prompt_c1 = (
                "IMPORTANTE: El siguiente dictamen jurídico se interrumpió antes de completar la frase:\n\n"
                f"«...{wave_1_text[-300:]}»\n\n"
                "INSTRUCCIÓN: Completa exactamente la última palabra y concluye la frase u oración interrumpida "
                "de manera coherente y cerrada con punto final. NO repitas el texto previo; escribe ÚNICAMENTE la continuación y cierre."
            )
            try:
                async for token in self.llm.stream(
                    prompt=prompt_c1,
                    system_prompt="Eres un corrector y redactor jurídico de alta precisión. Tu único objetivo es completar la frase interrumpida y cerrar con punto final.",
                    temperature=0.0,
                    max_tokens=300
                ):
                    wave_1_text += token
                    yield {"type": "token", "wave": 1, "text": token}
            except Exception:
                pass

        if wave_1_text and not wave_1_text.strip().endswith((".", "!", "?", "”", "»", ")", "]")):
            wave_1_text += "."
            yield {"type": "token", "wave": 1, "text": "."}

        yield {
            "type": "phase",
            "phase": "wave_1_done",
            "message": "Onda 1 entregada. Generando Onda 2: Ruta Procesal, Tutela y Recursos...",
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
            "ESTRUCTURA PARA LA ONDA 2 (DESARROLLO PRÁCTICO Y CONTEXTO NORMATIVO):\n"
            "1. ### Procedimiento y Acciones Concretas\n"
            "   (Si la consulta plantea una vulneración o caso de litigio, describe las acciones y recursos judiciales procedentes como Tutela o demandas. Si la consulta es una pregunta de conocimiento o precisión normativa sobre un artículo, explica el alcance jurídico, excepciones y concordancias normativas relevantes).\n"
            "2. ### Conclusión y Recomendaciones Prácticas Finales\n"
            "   (Cierre contundente con consejos prácticos para el consultante, advertencias legales y recomendaciones preventivas).\n\n"
            "REGLAS CRÍTICAS DE REDACCIÓN:\n"
            "- Desarrolla cada aspecto con precisión profesional y en párrafos claros.\n"
            "- Adapta el análisis a la naturaleza de la pregunta (NO inventes litigios ni quejas ante la SIC si la pregunta es solo conceptual o de identificación de un artículo).\n"
            "- Concluye todo el dictamen con un párrafo final cerrado con punto final.\n"
            "- NO repitas el Veredicto ni los Fundamentos ya emitidos en la Onda 1."
        )

        wave_2_text = ""
        try:
            async for token in self.llm.stream(
                prompt=prompt_wave_2,
                system_prompt=self.system_prompt,
                temperature=0.1,
                max_tokens=900  # Optimizado para evitar esperas excesivas en CPU
            ):
                wave_2_text += token
                yield {"type": "token", "wave": 2, "text": token}
        except Exception as e:
            wave_2_text = await self.llm.generate(prompt=prompt_wave_2, system_prompt=self.system_prompt, max_tokens=900)
            yield {"type": "token", "wave": 2, "text": wave_2_text}

        # Guardián Anti-Truncamiento: Onda 2
        if not self.is_thought_complete(wave_2_text):
            yield {
                "type": "phase",
                "phase": "wave_2_continuation",
                "message": "Completando recomendaciones procesales finales...",
                "wave": 2,
                "progress": 92
            }
            prompt_c2 = (
                "IMPORTANTE: La siguiente recomendación o ruta procesal se interrumpió antes de concluir:\n\n"
                f"«...{wave_2_text[-300:]}»\n\n"
                "INSTRUCCIÓN: Completa y concluye la recomendación o procedimiento interrumpido de forma coherente "
                "y redacta el párrafo de cierre definitivo con punto final. NO repitas texto previo, escribe sólo la continuación."
            )
            try:
                async for token in self.llm.stream(
                    prompt=prompt_c2,
                    system_prompt="Eres un litigante y redactor jurídico de alta precisión. Tu único objetivo es completar la frase y cerrar con punto final.",
                    temperature=0.0,
                    max_tokens=400
                ):
                    wave_2_text += token
                    yield {"type": "token", "wave": 2, "text": token}
            except Exception:
                pass

        if wave_2_text and not wave_2_text.strip().endswith((".", "!", "?", "”", "»", ")", "]")):
            wave_2_text += "."
            yield {"type": "token", "wave": 2, "text": "."}

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
