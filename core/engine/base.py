from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional

class BaseLLMEngine(ABC):
    """
    Contrato base desacoplado para cualquier motor de inferencia en Sadigua.
    Permite intercambiar Gemini, Ollama o cualquier otro motor sin tocar la lógica de negocio.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """Genera una respuesta completa."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Transmite la respuesta token por token en tiempo real."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Any,
        system_prompt: str = "",
        temperature: float = 0.0
    ) -> Any:
        """Genera una respuesta validada contra un esquema Pydantic (cero errores de formato)."""
        pass
