import os
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar .env manualmente si existe para no depender obligatoriamente de python-dotenv
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass

class Settings(BaseModel):
    # Proveedor LLM: Por defecto LOCAL (Soberano)
    LLM_PROVIDER: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "local"))

    # Compuerta de Soberanía (Air-Gap Gate)
    # Por defecto FALSE: Aunque exista GEMINI_API_KEY, no sale a la nube sin permiso explícito en el backend
    CLOUD_EGRESS_ENABLED: bool = Field(default_factory=lambda: os.getenv("CLOUD_EGRESS_ENABLED", "false").lower() == "true")

    # Gemini (Cloud)
    GEMINI_API_KEY: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    GEMINI_MODEL: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))

    # Local (Ollama / Llama.cpp)
    LOCAL_BASE_URL: str = Field(default_factory=lambda: os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1"))
    LOCAL_MODEL: str = Field(default_factory=lambda: os.getenv("LOCAL_MODEL", "qwen2.5:7b-instruct"))
    LOCAL_API_KEY: str = Field(default_factory=lambda: os.getenv("LOCAL_API_KEY", "ollama"))

    # Cartucho Activo
    ACTIVE_CARTRIDGE: str = Field(default_factory=lambda: os.getenv("ACTIVE_CARTRIDGE", "legal_co"))

    # Rutas del Sistema
    BASE_DIR: Path = BASE_DIR
    VAULT_PATH: Path = BASE_DIR / "vault"
    DATA_PATH: Path = BASE_DIR / "data"
    CARTRIDGES_PATH: Path = BASE_DIR / "cartridges"

    # Parámetros RAG
    EMBEDDING_MODEL: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"))
    RERANKER_MODEL: str = Field(default_factory=lambda: os.getenv("RERANKER_MODEL", "ms-marco-TinyBERT-L-2-v2"))
    RAG_TOP_K: int = 5
    RAG_SCORE_THRESHOLD: float = 0.60

    # Gateway API
    HOST: str = "0.0.0.0"
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "7837")))

settings = Settings()

# Asegurar directorios esenciales
settings.VAULT_PATH.mkdir(parents=True, exist_ok=True)
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
settings.CARTRIDGES_PATH.mkdir(parents=True, exist_ok=True)
