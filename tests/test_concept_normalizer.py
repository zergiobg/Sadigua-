"""
Pruebas Unitarias para el Normalizador Conceptual de Consultas Jurídicas
y el Interceptor de Antesala (Precedent Intent Check).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.memory.concept_normalizer import LegalConceptNormalizer
from core.memory.semantic_cache import SemanticPrecedentCache
from core.memory.vault_manager import ObsidianVaultManager
from fastapi.testclient import TestClient
from gateway.api import app

def test_legal_concept_normalization():
    norm = LegalConceptNormalizer()

    # Normalización de tildes, errores tipográficos y sinónimos
    clean_w = norm.clean_word("debor")
    assert clean_w == "debo"

    stripped = norm.strip_accents("vendió")
    assert stripped == "vendio"

    concepts = norm.extract_canonical_concepts("¿Qué debo hacer si descubro que una empresa vendió mis datos sin mi autorización?")
    assert "autorizacion" in concepts
    assert "venta" in concepts
    assert "datos" in concepts
    assert "responsable" in concepts

def test_user_screenshot_four_questions_similarity():
    """
    Verifica que las 4 preguntas de la captura del usuario sean reconocidas
    con alta afinidad conceptual (similitud >= 0.60) superando errores ortográficos,
    variaciones léxicas y giros de redacción.
    """
    norm = LegalConceptNormalizer()

    q1 = "¿Qué debo hacer si descubro que una empresa vendió mis datos personales sin mi autorización?"
    q2 = "¿Qué puedo hacer si una empresa vendió mis datos personales?"
    q3 = "que debor hacer si me doy cuenta que una empresa vendio mis datos"
    q4 = "que pasa si alguien vende mis datos? que puedo hacer?..."

    score_1_2 = norm.similarity(q1, q2)
    score_1_3 = norm.similarity(q1, q3)
    score_1_4 = norm.similarity(q1, q4)

    print(f"Similitud Q1 vs Q2: {score_1_2:.3f}")
    print(f"Similitud Q1 vs Q3: {score_1_3:.3f}")
    print(f"Similitud Q1 vs Q4: {score_1_4:.3f}")

    assert score_1_2 >= 0.60, f"Q1 vs Q2 falló umbral: {score_1_2}"
    assert score_1_3 >= 0.60, f"Q1 vs Q3 falló umbral: {score_1_3}"
    assert score_1_4 >= 0.60, f"Q1 vs Q4 falló umbral: {score_1_4}"

    # Pregunta conceptualmente no relacionada debe dar bajo puntaje (< 0.25)
    q_unrelated = "¿Cuál es el término perentorio para contestar una demanda ejecutiva singular?"
    score_unrelated = norm.similarity(q1, q_unrelated)
    print(f"Similitud Q1 vs No Relacionada: {score_unrelated:.3f}")
    assert score_unrelated < 0.25, f"Pregunta no relacionada dio score demasiado alto: {score_unrelated}"

def test_semantic_cache_precedent_candidate_interceptor():
    vault = ObsidianVaultManager()
    cache = SemanticPrecedentCache(vault_manager=vault)

    # Buscar candidato para una pregunta con variación léxica
    res = cache.find_candidate_precedent("que debor haser si una compania vende mis datos", threshold=0.55)
    assert res is not None
    assert res["found"] is True
    assert "datos" in res["matched_query"].lower() or "vend" in res["matched_query"].lower()
    assert res["similarity"] >= 0.55
    assert "preview" in res
    assert "note_id" in res

def test_api_check_intent_endpoint():
    client = TestClient(app)
    response = client.post("/api/chat/check-intent", json={
        "message": "que pasa si alguien vende mis datos personales?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "found" in data
    if data["found"]:
        assert "matched_query" in data
        assert "similarity" in data
        assert "note_id" in data
        assert "preview" in data

def test_api_precedent_answer_endpoint():
    client = TestClient(app)
    # Primero obtener un note_id real desde las consultas
    resp_list = client.get("/api/vault/consultas")
    assert resp_list.status_code == 200
    consultas = resp_list.json().get("consultas", [])
    if consultas:
        sample_id = consultas[0]["note_id"]
        res = client.post("/api/chat/precedent-answer", json={
            "note_id": sample_id,
            "query": "consulta de prueba para precedente"
        })
        assert res.status_code == 200
        ans = res.json()
        assert ans["status"] == "success"
        assert len(ans["answer"]) > 0

if __name__ == "__main__":
    test_legal_concept_normalization()
    test_user_screenshot_four_questions_similarity()
    test_semantic_cache_precedent_candidate_interceptor()
    test_api_check_intent_endpoint()
    test_api_precedent_answer_endpoint()
    print("Todas las pruebas de normalización conceptual y antesala superadas exitosamente.")
