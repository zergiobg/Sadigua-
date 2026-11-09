"""
SADIGUA - Script de Descarga y Verificación de Modelos Locales Qwen
"""

import sys
import httpx
import time
from config.settings import settings

def check_ollama_service(base_url="http://localhost:11434"):
    try:
        r = httpx.get(f"{base_url}/api/version", timeout=3.0)
        if r.status_code == 200:
            print(f"[OK] Servicio Ollama activo en {base_url} (Version: {r.json().get('version')})")
            return True
    except Exception:
        pass
    return False

def list_installed_models(base_url="http://localhost:11434"):
    try:
        r = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return models
    except Exception:
        pass
    return []

def pull_model(model_name="qwen2.5:14b-instruct", base_url="http://localhost:11434"):
    print(f"[*] Solicitando descarga del modelo local: '{model_name}'...")
    print("    (Este proceso descargara los pesos GGUF optimizados para tu procesador Intel Core Ultra)")
    
    url = f"{base_url}/api/pull"
    with httpx.stream("POST", url, json={"name": model_name}, timeout=None) as response:
        for line in response.iter_lines():
            if line:
                import json
                try:
                    data = json.loads(line)
                    status = data.get("status", "")
                    completed = data.get("completed", 0)
                    total = data.get("total", 0)
                    if total > 0:
                        pct = round((completed / total) * 100, 1)
                        print(f"\r    -> {status}: {pct}% ({round(completed/(1024*1024), 1)} MB de {round(total/(1024*1024), 1)} MB)", end="")
                    else:
                        print(f"\r    -> {status}...", end="")
                except Exception:
                    pass
    print(f"\n[OK] Modelo '{model_name}' descargado e instalado con exito en tu equipo.")

if __name__ == "__main__":
    target_model = sys.argv[1] if len(sys.argv) > 1 else settings.LOCAL_MODEL
    print("=" * 65)
    print("SADIGUA - INSTALADOR DE MODELO SOBERANO QWEN")
    print("=" * 65)

    if not check_ollama_service():
        print("[!] No se detecta el servicio de Ollama activo en http://localhost:11434")
        print("    Asegúrate de que Ollama esté iniciado.")
        sys.exit(1)

    installed = list_installed_models()
    print(f"[*] Modelos locales actualmente en memoria: {installed}")

    if target_model in installed or any(target_model in m for m in installed):
        print(f"[OK] El modelo '{target_model}' ya se encuentra instalado localmente.")
    else:
        pull_model(target_model)
