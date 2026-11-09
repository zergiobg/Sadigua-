import os
import shutil
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient

from core.memory.vault_manager import ObsidianVaultManager
from core.memory.semantic_cache import SemanticPrecedentCache
from core.engine.base import BaseLLMEngine
from core.agents.orchestrator import SadiguaOrchestrator
from gateway.api import app
from typing import AsyncGenerator, Optional, Any

class MockDelayedStreamingLLM(BaseLLMEngine):
    """Motor simulado con tokens continuos para validar parada en vuelo."""
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.1, max_tokens: Optional[int] = None) -> str:
        return "Respuesta simulada de prueba para memoria efímera."

    async def stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.1, max_tokens: Optional[int] = None) -> AsyncGenerator[str, None]:
        for i in range(10):
            await asyncio.sleep(0.01)
            yield f"token_{i} "

    async def generate_structured(self, prompt: str, response_model: Any, system_prompt: str = "", temperature: float = 0.0) -> Any:
        return None

def test_stop_generation_orchestrator():
    """Valida que la señal de parada interrumpe la síntesis en curso inmediatamente."""
    test_vault = ObsidianVaultManager(vault_path=Path("vault_stop_test"))
    llm = MockDelayedStreamingLLM()
    orch = SadiguaOrchestrator(
        cartridge_name="legal_co",
        llm_engine=llm,
        vault_manager=test_vault
    )

    async def run_stop():
        events = []
        gen = orch.answer_progressive_stream("Consulta de prueba para detener")
        first_event = await gen.__anext__()
        events.append(first_event)

        # El usuario hace clic en el botón de STOP mientras se genera la síntesis
        orch.request_stop()

        async for event in gen:
            events.append(event)
            if event.get("type") == "stopped":
                break

        types = [e.get("type") for e in events]
        assert "stopped" in types, f"La generación debió emitir un evento 'stopped', se recibió: {types}"
        assert "done" not in types, "No debió completar con 'done' al ser abortada"

    try:
        asyncio.run(run_stop())
    finally:
        if Path("vault_stop_test").exists():
            shutil.rmtree("vault_stop_test")

def test_ephemeral_query_does_not_save_to_memory():
    """Valida que con include_in_memory=False no se guarde nota en Obsidian ni índice."""
    test_vault = ObsidianVaultManager(vault_path=Path("vault_ephemeral_test"))
    llm = MockDelayedStreamingLLM()
    orch = SadiguaOrchestrator(
        cartridge_name="legal_co",
        llm_engine=llm,
        vault_manager=test_vault
    )

    async def run_ephemeral():
        # Ejecutar con include_in_memory=False
        res = await orch.answer("Consulta confidencial y efímera", include_in_memory=False)
        assert res["in_memory"] is False
        assert res["note_id"] is None

        # Verificar que no hay archivos en vault_ephemeral_test/consultas
        consultas_dir = Path("vault_ephemeral_test") / "consultas"
        if consultas_dir.exists():
            files = list(consultas_dir.glob("*.md"))
            assert len(files) == 0, f"No debió crearse ninguna nota en bóveda: {files}"

    try:
        asyncio.run(run_ephemeral())
    finally:
        if Path("vault_ephemeral_test").exists():
            shutil.rmtree("vault_ephemeral_test")

def test_api_stop_and_delete_precedent_endpoints():
    """Valida los endpoints REST /api/chat/stop y DELETE /api/vault/consultas/{note_id}."""
    client = TestClient(app)

    # 1. Probar POST /api/chat/stop
    stop_res = client.post("/api/chat/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "stopped"

    # 2. Guardar un precedente simulado en la caché
    async def create_dummy_precedent():
        from gateway.api import orchestrator
        return await orchestrator.semantic_cache.store_precedent(
            query="¿Cómo eliminar este precedente?",
            answer="Respuesta temporal que será removida a petición del usuario.",
            sources=[],
            cartridge_name="legal_co",
            grounding_status="✓ Prueba"
        )
    note_path = asyncio.run(create_dummy_precedent())
    note_id = note_path.stem
    assert note_path.exists()

    # 3. Eliminarlo usando DELETE /api/vault/consultas/{note_id}
    del_res = client.delete(f"/api/vault/consultas/{note_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
    assert not note_path.exists(), "El archivo en bóveda debió ser eliminado"
