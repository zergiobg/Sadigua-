import os
import tempfile
from pathlib import Path
from core.rag.mutation_engine import LexMutationEngine
from core.rag.reranker import PrecisionReranker
from core.memory.vault_manager import ObsidianVaultManager
from fastapi.testclient import TestClient
from gateway.api import app

def test_sqlite_mutation_storage_and_query():
    db_path = Path(tempfile.gettempdir()) / "sadigua_unit_test_mutations.db"
    if db_path.exists():
        try:
            os.remove(db_path)
        except Exception:
            pass

    try:
        engine = LexMutationEngine(db_path=db_path)
        
        mut_id = engine.record_mutation(
            source_doc="Sentencia SU-045 de 2026",
            target_norm="Sentencia T-200 de 2018",
            mutation_type="OVERRULING",
            regla_anterior="El término de prescripción corría desde la ocurrencia del hecho dañoso sin importar conocimiento.",
            regla_nueva="El término de prescripción corre únicamente a partir del conocimiento fehaciente del titular afectado.",
            autoridad="Corte Constitucional - Sala Plena",
            efectos="Hacia el futuro (Ex nunc)",
            curator_notes="Unificación de jurisprudencia en materia de habeas data y responsabilidad civil."
        )
        assert mut_id > 0, "El ID de la mutación debe ser mayor a 0"

        # Listar mutaciones
        mutations = engine.list_mutations()
        assert len(mutations) == 1
        assert mutations[0]["target_norm"] == "Sentencia T-200 de 2018"
        assert mutations[0]["mutation_type"] == "OVERRULING"
        assert "conocimiento fehaciente" in mutations[0]["regla_nueva"]

        # Búsqueda por coincidencia
        results_target = engine.find_mutations_for_norm("T-200")
        assert len(results_target) == 1
        assert results_target[0]["id"] == mut_id

        results_keyword = engine.find_mutations_for_norm("prescripción")
        assert len(results_keyword) == 1

        results_empty = engine.find_mutations_for_norm("codigo_inexistente_xyz")
        assert len(results_empty) == 0
    finally:
        if db_path.exists():
            try:
                os.remove(db_path)
            except Exception:
                pass

def test_obsidian_vault_sync_mutation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        vault = ObsidianVaultManager(vault_path=Path(tmp_dir))
        mutation = {
            "source_doc": "Sentencia SU-045 de 2026",
            "target_norm": "Sentencia T-200 de 2018",
            "mutation_type": "OVERRULING",
            "regla_anterior": "Regla superada",
            "regla_nueva": "Regla nueva unificada",
            "autoridad": "Corte Constitucional",
            "fecha_mutacion": "2026-11-09",
            "efectos": "Hacia el futuro (Ex nunc)"
        }
        res = vault.record_precedent_mutation(mutation)
        
        # Verificar nota de la norma superada
        target_note = vault.get_note("jurisprudencia", res["target_id"])
        assert target_note is not None
        assert target_note["metadata"]["estado"] == "SUPERADO"
        assert target_note["metadata"]["superceded_by"] == "Sentencia SU-045 de 2026"
        assert "PRECEDENTE SUPERADO" in target_note["content"]

        # Verificar nota de la norma vigente
        source_note = vault.get_note("jurisprudencia", res["source_id"])
        assert source_note is not None
        assert source_note["metadata"]["estado"] == "VIGENTE"
        assert res["target_id"] in source_note["content"]

def test_reranker_temporal_weighting():
    reranker = PrecisionReranker()
    docs = [
        {
            "id": "doc_vigente",
            "source": "Sentencia SU-045 de 2026",
            "articulo": "Regla Vigente",
            "content": "La prescripción corre desde el conocimiento efectivo del titular del dato.",
            "vigencia_status": "VIGENTE",
            "lexical_score": 5.0,
            "vector_score": 0.8
        },
        {
            "id": "doc_superado",
            "source": "Sentencia T-200 de 2018",
            "articulo": "Regla Anterior",
            "content": "La prescripción corre desde el hecho independientemente del conocimiento.",
            "vigencia_status": "SUPERADO",
            "lexical_score": 5.0,
            "vector_score": 0.8
        }
    ]

    # Consulta común: Debe ganar la norma vigente (la norma superada recibe penalización 0.20x)
    reranked_common = reranker.rerank("¿Cuándo prescribe la acción de datos?", docs, top_n=2)
    assert reranked_common[0]["id"] == "doc_vigente", "El documento vigente debe rankear primero"
    assert reranked_common[0]["rerank_score"] > reranked_common[1]["rerank_score"]

    # Consulta histórica: Debe priorizarse la norma superada / histórica (recibe boost 1.80x)
    reranked_hist = reranker.rerank("¿Cuál era el criterio jurisprudencial histórico derogado antes de 2026?", docs, top_n=2)
    assert reranked_hist[0]["id"] == "doc_superado", "En consulta histórica debe priorizarse el precedente superado"

def test_api_mutation_endpoints():
    client = TestClient(app)
    
    # 1. Registrar mutación vía API
    payload = {
        "source_doc": "Sentencia C-500 de 2026",
        "target_norm": "Artículo 999 del Código de Comercio",
        "mutation_type": "INEXEQUIBILIDAD",
        "regla_anterior": "Facultad sancionatoria sin debido proceso sumario previo.",
        "regla_nueva": "Exigencia inexcusable de traslado y audiencia previa de descargo.",
        "autoridad": "Corte Constitucional",
        "fecha_mutacion": "2026-11-09",
        "efectos": "Inmediato (Ex tunc)",
        "curator_notes": "Control de constitucionalidad."
    }
    post_res = client.post("/api/jurisprudencia/record-mutation", json=payload)
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["status"] == "success"
    assert "mutation_id" in data

    # 2. Consultar listado de mutaciones
    get_res = client.get("/api/jurisprudencia/mutations")
    assert get_res.status_code == 200
    mutations = get_res.json()
    assert isinstance(mutations, list)
    assert any(m["target_norm"] == "Artículo 999 del Código de Comercio" for m in mutations)

    # 3. Filtrar por término
    filter_res = client.get("/api/jurisprudencia/mutations?q=999")
    assert filter_res.status_code == 200
    filtered = filter_res.json()
    assert len(filtered) >= 1
    assert filtered[0]["target_norm"] == "Artículo 999 del Código de Comercio"
