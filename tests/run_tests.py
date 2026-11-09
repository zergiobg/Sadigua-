import sys
import os
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_sadigua_core import (
    test_pii_anonymizer,
    test_obsidian_vault_manager,
    test_legal_hierarchical_chunker,
    test_pure_bm25_exact_match,
    test_grounding_validator,
    test_engine_factory
)
from tests.test_api_endpoints import (
    test_api_health_and_status,
    test_api_static_web_serving,
    test_api_cartridges_and_docs,
    test_api_vault_crud,
    test_api_vault_consultas,
    test_api_chat_progressive
)
from tests.test_progressive_and_cache import (
    test_semantic_precedent_cache,
    test_progressive_stream_orchestrator
)
from tests.test_thought_completion import test_thought_completion_detector

def run_all():
    tests = [
        ("PII Anonymizer (Ley 1581)", test_pii_anonymizer),
        ("Cerebro Obsidiano (Vault Markdown + Frontmatter)", test_obsidian_vault_manager),
        ("Legal Hierarchical Chunker", test_legal_hierarchical_chunker),
        ("Pure BM25 Exact Match Engine", test_pure_bm25_exact_match),
        ("Grounding Validator (Anti-Alucinaciones)", test_grounding_validator),
        ("Dual-Engine Factory (Gemini + Local)", test_engine_factory),
        ("Caché Semántico de Precedentes (Similitud Coseno)", test_semantic_precedent_cache),
        ("Orquestador Progresivo Multi-Onda & Telemetría", test_progressive_stream_orchestrator),
        ("Guardián Anti-Truncamiento & Cierre de Ideas", test_thought_completion_detector),
        ("API REST: Estado del Sistema & Health", test_api_health_and_status),
        ("API REST: Servidor Web Estático (HTML/CSS/JS)", test_api_static_web_serving),
        ("API REST: Gestión de Cartuchos y Documentos", test_api_cartridges_and_docs),
        ("API REST: CRUD de Bóveda Obsidian (Expedientes)", test_api_vault_crud),
        ("API REST: Catálogo de Precedentes / Consultas", test_api_vault_consultas),
        ("API REST: Endpoint Streaming SSE Progresivo", test_api_chat_progressive),
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("EJECUTANDO BANCO DE PRUEBAS DEL NÚCLEO SADIGUA")
    print("=" * 60)

    for name, test_func in tests:
        try:
            test_func()
            print(f"[PASÓ]  {name}")
            passed += 1
        except Exception as e:
            print(f"[FALLÓ] {name} -> {e}")
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"RESUMEN: {passed} superados, {failed} fallidos.")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_all()
