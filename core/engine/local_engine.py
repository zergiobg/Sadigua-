import json
from typing import AsyncGenerator, Any, Optional
import httpx
from core.engine.base import BaseLLMEngine
from config.settings import settings

class LocalEngine(BaseLLMEngine):
    """
    Implementación del motor usando el runtime local soberano Ollama.
    Optimizado para procesadores Intel Core Ultra con asignación explícita de hilos CPU (AVX2).
    100% Offline, costo cero y máxima privacidad.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 300.0,
        num_threads: Optional[int] = None
    ):
        raw_url = (base_url or settings.LOCAL_BASE_URL).rstrip("/")
        # Si la URL viene con /v1 al final, limpiarla para usar la API nativa de alto rendimiento de Ollama
        if raw_url.endswith("/v1"):
            raw_url = raw_url[:-3]
        self.base_url = raw_url
        self.model = model or settings.LOCAL_MODEL
        self.timeout = timeout or 300.0
        
        # Auto-calibración dinámica de hilos de CPU según el hardware detectado
        if num_threads is None:
            try:
                from core.hardware.detector import HardwareProfiler
                hw = HardwareProfiler.profile()
                self.num_threads = hw["optimal_threads"]
            except Exception:
                self.num_threads = 8
        else:
            self.num_threads = num_threads

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": temperature,
                "num_thread": self.num_threads,
                "num_predict": max_tokens or 2048,
                "num_ctx": 4096,
                "repeat_penalty": 1.15,
                "top_p": 0.9
            }
        }

        url = f"{self.base_url}/api/chat"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
            except httpx.ConnectError:
                raise ConnectionError(
                    f"No se pudo conectar al motor local en {self.base_url}. "
                    "Asegúrate de que Ollama esté corriendo."
                )

    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": -1,
            "options": {
                "temperature": temperature,
                "num_thread": self.num_threads,
                "num_predict": max_tokens or 2048,
                "num_ctx": 4096,
                "repeat_penalty": 1.15,
                "top_p": 0.9
            }
        }

        url = f"{self.base_url}/api/chat"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            except httpx.ConnectError:
                raise ConnectionError(
                    f"No se pudo conectar al motor local en {self.base_url}. "
                    "Asegúrate de que Ollama esté corriendo."
                )

    async def generate_structured(
        self,
        prompt: str,
        response_model: Any,
        system_prompt: str = "",
        temperature: float = 0.0
    ) -> Any:
        schema = response_model.model_json_schema()
        instruction = (
            f"{system_prompt}\n\n"
            "DEBES responder estrictamente en formato JSON válido respetando el siguiente esquema:\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        raw_text = await self.generate(
            prompt=prompt,
            system_prompt=instruction,
            temperature=temperature
        )
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return response_model.model_validate_json(cleaned.strip())
