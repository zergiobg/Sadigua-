import os
from typing import AsyncGenerator, Any, Optional
from google import genai
from google.genai import types
from core.engine.base import BaseLLMEngine
from config.settings import settings

class GeminiEngine(BaseLLMEngine):
    """
    Implementación del motor usando Google Gemini (Modo Cloud Híbrido).
    Ofrece máxima velocidad, enorme ventana de contexto y soporte para evaluación de precisión.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model = model or settings.GEMINI_MODEL
        if not self.api_key:
            # Fallback para permitir instanciar sin API key si no se ha llamado aún
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)

    def _ensure_client(self):
        if not self.client:
            api_key = self.api_key or os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY no está configurada. Por favor establécela en el archivo .env o en variables de entorno."
                )
            self.client = genai.Client(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        self._ensure_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt if system_prompt else None,
            max_output_tokens=max_tokens
        )
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        return response.text or ""

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        self._ensure_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt if system_prompt else None,
            max_output_tokens=max_tokens
        )
        response_stream = await self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=config
        )
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    async def generate_structured(
        self,
        prompt: str,
        response_model: Any,
        system_prompt: str = "",
        temperature: float = 0.0
    ) -> Any:
        self._ensure_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_prompt if system_prompt else None,
            response_mime_type="application/json",
            response_schema=response_model
        )
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        # Devolver la instancia del modelo parseada
        if hasattr(response, 'parsed') and response.parsed is not None:
            return response.parsed
        return response_model.model_validate_json(response.text)
