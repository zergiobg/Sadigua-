from fastapi.testclient import TestClient
from gateway.api import app

def test_api_health_and_status():
    client = TestClient(app)
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["active_cartridge"] == "legal_co"

def test_api_static_web_serving():
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    assert "SADIGUA" in res.text

    res_css = client.get("/css/styles.css")
    assert res_css.status_code == 200
    assert "--primary-blue" in res_css.text

    res_js = client.get("/js/app.js")
    assert res_js.status_code == 200
    assert "loadSystemStatus" in res_js.text

def test_api_cartridges_and_docs():
    client = TestClient(app)
    carts = client.get("/api/cartridges").json()
    assert len(carts) >= 2
    assert any(c["id"] == "legal_co" for c in carts)

    docs = client.get("/api/documents").json()
    assert len(docs) >= 3

def test_api_vault_crud():
    client = TestClient(app)
    # List notes
    notes = client.get("/api/vault/notes").json()
    assert isinstance(notes, list)

    # Save note via API
    new_note = {
        "category": "expedientes",
        "note_id": "test_api_expediente",
        "title": "Expediente Creado por API",
        "content": "Hechos de prueba jurídica.",
        "tags": ["test", "api"]
    }
    save_res = client.post("/api/vault/notes", json=new_note)
    assert save_res.status_code == 200
    assert save_res.json()["status"] == "saved"

    # Read back
    detail_res = client.get("/api/vault/notes/expedientes/test_api_expediente")
    assert detail_res.status_code == 200
    assert detail_res.json()["metadata"]["titulo"] == "Expediente Creado por API"

def test_api_vault_consultas():
    client = TestClient(app)
    res = client.get("/api/vault/consultas")
    assert res.status_code == 200
    data = res.json()
    assert "total_consultas" in data
    assert "consultas" in data
    assert isinstance(data["consultas"], list)

def test_api_chat_progressive():
    from unittest.mock import patch

    async def mock_stream(query):
        yield {"type": "phase", "phase": "wave_1_start", "message": "Iniciando"}
        yield {"type": "token", "wave": 1, "text": "Prueba"}
        yield {"type": "done"}

    with patch("gateway.api.orchestrator.answer_progressive_stream", side_effect=mock_stream):
        client = TestClient(app)
        with client.stream("POST", "/api/chat/progressive", json={"message": "Test"}) as res:
            assert res.status_code == 200
            assert "text/event-stream" in res.headers["content-type"]
            lines = list(res.iter_lines())
            assert any("wave_1_start" in l for l in lines)

