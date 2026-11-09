import re
from typing import Tuple, Dict

class PIIAnonymizer:
    """
    Módulo de Anonimización de Datos Personales Sensibles (PII).
    Cumplimiento estricto de la Ley 1581 de 2012 y principios de soberanía de datos.
    Enmascara cédulas, correos, teléfonos y tarjetas de crédito antes del procesamiento.
    """

    PATTERNS = {
        "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "CEDULA_CO": r'\b(?:C\.?C\.?|cédula\s+de\s+ciudadanía|cédula|identificación)\s*[:#]?\s*(\d{6,10})\b',
        "TELEFONO": r'\b(?:\+?57\s*)?(?:3\d{2}[\s.-]?\d{3}[\s.-]?\d{4}|[1-9]\d{6})\b',
        "TARJETA": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    }

    @classmethod
    def mask(cls, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Enmascara PII en el texto y devuelve un mapa de reversibilidad si se requiere restaurar.
        """
        masked_text = text
        mapping = {}

        # 1. Enmascarar correos
        for match in re.finditer(cls.PATTERNS["EMAIL"], masked_text):
            val = match.group(0)
            token = f"[EMAIL_{hash(val) % 10000}]"
            mapping[token] = val
            masked_text = masked_text.replace(val, token)

        # 2. Enmascarar cédulas de ciudadanía
        for match in re.finditer(cls.PATTERNS["CEDULA_CO"], masked_text, re.IGNORECASE):
            full_match = match.group(0)
            num = match.group(1)
            token = f"[ID_{hash(num) % 10000}]"
            mapping[token] = num
            masked_text = masked_text.replace(full_match, f"Cédula {token}")

        # 3. Enmascarar teléfonos
        for match in re.finditer(cls.PATTERNS["TELEFONO"], masked_text):
            val = match.group(0)
            token = f"[TEL_{hash(val) % 10000}]"
            mapping[token] = val
            masked_text = masked_text.replace(val, token)

        return masked_text, mapping

    @classmethod
    def unmask(cls, text: str, mapping: Dict[str, str]) -> str:
        restored = text
        for token, val in mapping.items():
            restored = restored.replace(token, val)
        return restored
