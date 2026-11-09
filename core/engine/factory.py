from core.engine.base import BaseLLMEngine
from core.engine.gemini_engine import GeminiEngine
from core.engine.local_engine import LocalEngine
from config.settings import settings

def get_llm_engine(provider: str = None) -> BaseLLMEngine:
    """
    Factoría para instanciar el motor de lenguaje con Compuerta de Soberanía (Air-Gap Gate).
    Por defecto opera 100% LOCAL. La salida a la nube (Gemini) requiere permiso explícito.
    """
    active_provider = (provider or settings.LLM_PROVIDER).lower()

    if active_provider == "local":
        return LocalEngine()

    elif active_provider == "gemini":
        # Verificación estricta de la Compuerta de Soberanía
        if not settings.CLOUD_EGRESS_ENABLED:
            raise PermissionError(
                "COMPUERTA DE SOBERANÍA ACTIVA: La salida a la nube (Gemini) está BLOQUEADA por política de seguridad. "
                "Aunque la API Key esté cargada en .env, debes activar explícitamente el interruptor "
                "'Permitir Salida Cloud' en el Centro MLOps o en el backend."
            )
        return GeminiEngine()

    else:
        raise ValueError(
            f"Proveedor de LLM desconocido: '{active_provider}'. "
            "Los proveedores soportados son 'local' o 'gemini'."
        )
