import re
from typing import List, Dict, Any, Tuple

class GroundingValidator:
    """
    Validador Anti-Alucinaciones (Self-RAG Grounding Validator).
    Examina si la respuesta generada cita normas reales y si dichas normas
    están presentes en el contexto documental recuperado.
    Distingue entre menciones afirmativas y declaraciones de ausencia de fuentes.
    """

    @staticmethod
    def validate(response_text: str, context_chunks: List[Dict[str, Any]]) -> Tuple[bool, str, List[str]]:
        lower_resp = response_text.lower()

        # Si el modelo explícitamente reconoció que la norma no se encuentra en el corpus
        absence_phrases = [
            "no se encuentra registro",
            "no dispongo de información",
            "no se dispone de",
            "no obra en el corpus",
            "no se encuentra en las fuentes",
            "no está en el corpus"
        ]
        has_absence_declaration = any(p in lower_resp for p in absence_phrases)

        if not context_chunks:
            if has_absence_declaration:
                return True, "El modelo reconoció correctamente la falta de fuentes.", []
            return False, "Alerta de alucinación: Respuesta afirmativa sin contexto documental de respaldo.", []

        # Extraer referencias normativas citadas (ej. "artículo 206", "ley 1581", etc.)
        cited_articles = set(re.findall(r'(?:artículo|ley|decreto|sentencia)\s+\d+[\.\w]*', response_text, re.IGNORECASE))
        context_corpus = " ".join([c.get("content", "") for c in context_chunks]).lower()

        unsupported_citations = []
        for cite in cited_articles:
            # Extraer solo el número
            num_match = re.search(r'\d+', cite)
            if num_match:
                num = num_match.group(0)
                # Si el número no está en el contexto recuperado
                if num not in context_corpus:
                    # Verificar si la frase donde aparece este artículo es una negación / declaración de ausencia
                    pattern = rf'(?:no se encuentra|no existe|no se dispone|no obra|no registra)[^.]*{re.escape(cite)}'
                    if not re.search(pattern, lower_resp, re.IGNORECASE):
                        unsupported_citations.append(cite)

        if unsupported_citations:
            return False, f"Alucinación detectada: Citaciones no respaldadas en el corpus ({', '.join(unsupported_citations)})", list(cited_articles)

        return True, "Respuesta debidamente respaldada en el contexto documental.", list(cited_articles)
