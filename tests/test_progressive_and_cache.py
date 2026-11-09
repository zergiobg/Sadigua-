import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.memory.vault_manager import ObsidianVaultManager
from core.memory.semantic_cache import SemanticPrecedentCache
from core.engine.base import BaseLLMEngine
from core.agents.orchestrator import SadiguaOrchestrator
from typing import AsyncGenerator, Optional, Any

class MockStreamingLLM(BaseLLMEngine):
    """Motor LLM simulado para pruebas unitarias de streaming progresivo."""
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.1, max_tokens: Optional[int] = None) -> str:
        return "Dictamen de prueba basado en el Artículo 15 de la Constitución Política."

    async def stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.1, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        tokens = ["Dictamen ", "jurídico: ", "el Artículo 15 ", "protege ", "la intimidad."]
        for t in tokens:
            await asyncio.sleep(0.01)
            yield t

    async def generate_structured(self, prompt: str, response_model: Any, system_prompt: str = "", temperature: float = 0.0) -> Any:
        return None

def test_semantic_precedent_cache():
    """Prueba el almacenamiento y recuperación de precedentes en vault/consultas/"""
    test_vault = ObsidianVaultManager(vault_path=Path("vault_test"))
    cache = SemanticPrecedentCache(vault_manager=test_vault, similarity_threshold=0.85)

    query = "¿Qué ocurre si una empresa vende mis datos sin autorización?"
    answer = "Según el Artículo 15 de la Constitución y la Ley 1581, es una infracción que acarrea sanciones de la SIC."
    sources = [{"source": "ley_1581_datos_soberania.md", "articulo": "ARTÍCULO 4", "section": "PRINCIPIOS"}]

    async def run_cache():
        # 1. Guardar precedente
        note_path = await cache.store_precedent(
            query=query,
            answer=answer,
            sources=sources,
            cartridge_name="legal_co",
            grounding_status="✓ Grounding Verificado"
        )
        assert note_path.exists(), "La nota del precedente no fue creada en disco"
        content = note_path.read_text(encoding="utf-8")
        assert "ARTÍCULO 4" in content or "ley_1581" in content
        assert "precedente" in content

        # 2. Consultar con la misma pregunta (Cache Hit)
        hit = await cache.check_precedent(query)
        assert hit is not None, "El chequeo de precedente debió ser exitoso (Hit)"
        assert hit["similarity"] >= 0.85, f"Similitud baja: {hit['similarity']}"
        assert hit["answer"] == answer

        # 3. Consultar con pregunta no relacionada (Cache Miss)
        miss = await cache.check_precedent("¿Cuál es la fórmula cuántica de la gravedad?")
        assert miss is None, "Una consulta no relacionada debió ser Cache Miss"

    asyncio.run(run_cache())

    # Limpiar vault_test
    import shutil
    if Path("vault_test").exists():
        shutil.rmtree("vault_test")
    if Path("data/consultas_index.json").exists():
        try:
            # mantener el índice limpio si fue creado para el test
            pass
        except Exception:
            pass

def test_progressive_stream_orchestrator():
    """Prueba la generación progresiva en ondas del orquestador."""
    import uuid
    mock_llm = MockStreamingLLM()
    orch = SadiguaOrchestrator(
        cartridge_name="legal_co",
        llm_engine=mock_llm
    )

    async def run_stream():
        query = f"¿Cuáles son los términos para resolver una tutela? {uuid.uuid4().hex[:6]}"
        events = []
        async for evt in orch.answer_progressive_stream(query):
            events.append(evt)

        # Validar secuencia de eventos
        types = [e["type"] for e in events]
        assert "phase" in types, "Falta evento de fase"
        assert "token" in types, "Faltan tokens de streaming"
        assert "done" in types, "Falta evento done"

        # Validar ondas
        phases = [e.get("phase") for e in events if e["type"] == "phase"]
        assert "wave_1_start" in phases, "No se inició Onda 1"
        assert "wave_1_done" in phases, "No finalizó Onda 1"
        assert "wave_2_start" in phases, "No se inició Onda 2"
        assert "wave_2_done" in phases, "No finalizó Onda 2"

        # Segunda consulta idéntica debe dar precedent_hit inmediato
        hit_events = []
        async for evt in orch.answer_progressive_stream(query):
            hit_events.append(evt)

        hit_types = [e["type"] for e in hit_events]
        assert "precedent_hit" in hit_types, "La segunda consulta debió dar precedent_hit"

    asyncio.run(run_stream())

if __name__ == "__main__":
    test_semantic_precedent_cache()
    print("[OK] test_semantic_precedent_cache")
    test_progressive_stream_orchestrator()
    print("[OK] test_progressive_stream_orchestrator")
