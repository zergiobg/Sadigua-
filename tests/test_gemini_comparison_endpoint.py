import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from gateway.api import app
from config.settings import settings

client = TestClient(app)

def test_system_status_reports_gemini_status():
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.json()
    assert "gemini_configured" in data
    assert "gemini_model" in data

def test_gemini_stream_without_key_reports_informative_sse():
    # Asegurar temporalmente que no hay key en settings ni en os.environ
    old_key = settings.GEMINI_API_KEY
    old_env = os.environ.pop("GEMINI_API_KEY", None)
    settings.GEMINI_API_KEY = ""
    try:
        res = client.post("/api/chat/gemini-stream", json={"message": "¿Qué es el juramento estimatorio?"})
        assert res.status_code == 200
        text = res.text
        assert "data:" in text
        assert "GEMINI_API_KEY" in text or "no configurada" in text
    finally:
        settings.GEMINI_API_KEY = old_key
        if old_env is not None:
            os.environ["GEMINI_API_KEY"] = old_env

def test_update_gemini_config_in_mlops():
    payload = {
        "gemini_api_key": "AIzaSyTestMockKeyForPedagogicalComparison12345",
        "gemini_model": "gemini-2.5-flash"
    }
    res = client.post("/api/system/config", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"]["gemini_configured"] is True
    assert settings.GEMINI_API_KEY == "AIzaSyTestMockKeyForPedagogicalComparison12345"

def run_tests():
    test_system_status_reports_gemini_status()
    test_gemini_stream_without_key_reports_informative_sse()
    test_update_gemini_config_in_mlops()

if __name__ == "__main__":
    run_tests()
    print("All comparison tests passed!")
