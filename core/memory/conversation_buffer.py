from typing import List, Dict, Any, Optional
from datetime import datetime

class ConversationBuffer:
    """
    Gestor de memoria a corto plazo en sesión.
    Mantiene la ventana de contexto de la conversación activa y permite compactar
    el historial antes de saturar el límite de tokens.
    """

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.messages: List[Dict[str, Any]] = []

    def add_user_message(self, content: str):
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim()

    def add_assistant_message(self, content: str, citations: Optional[List[str]] = None):
        self.messages.append({
            "role": "assistant",
            "content": content,
            "citations": citations or [],
            "timestamp": datetime.now().isoformat()
        })
        self._trim()

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def clear(self):
        self.messages = []

    def _trim(self):
        if len(self.messages) > self.max_messages:
            # Conservar los más recientes
            self.messages = self.messages[-self.max_messages:]
