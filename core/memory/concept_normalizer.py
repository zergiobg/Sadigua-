import re
import unicodedata
from typing import Set, List, Dict, Tuple
from difflib import SequenceMatcher

class LegalConceptNormalizer:
    """
    Normalizador Lingüístico y Extractor de Concepto Rector para Derecho Colombiano.
    Elimina tildes, corrige typos comunes, canóniza sinónimos y lematiza
    términos clave para identificar precedentes jurídicos equivalentes.
    """

    STOPWORDS: Set[str] = {
        "que", "qué", "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
        "y", "o", "a", "en", "para", "por", "si", "mi", "mis", "su", "sus", "sin",
        "con", "se", "del", "al", "es", "son", "como", "sobre", "mas", "más", "pero",
        "muy", "ante", "desde", "hasta", "hacia", "este", "esta", "estos", "estas",
        "donde", "dónde", "cuando", "cuándo", "quien", "quién", "cual", "cuál",
        "puedo", "podria", "podría", "debo", "deberia", "debería", "hacer", "hago",
        "pasa", "pasaria", "pasaría", "ocurre", "ocurriria", "ocurriría"
    }

    # Diccionario de canónización de sinónimos y raíces conceptuales jurídicas
    SYNONYM_MAP: Dict[str, str] = {
        # Consentimiento / Autorización
        "permiso": "autorizacion",
        "permisos": "autorizacion",
        "autorizacion": "autorizacion",
        "autorizaciones": "autorizacion",
        "consentimiento": "autorizacion",
        "aprobacion": "autorizacion",
        "anuencia": "autorizacion",
        "autorizo": "autorizacion",
        "autorice": "autorizacion",

        # Venta / Cesión / Tráfico de datos
        "vender": "venta",
        "vende": "venta",
        "venden": "venta",
        "vendio": "venta",
        "vendieron": "venta",
        "venta": "venta",
        "ventas": "venta",
        "comercializo": "venta",
        "comercializar": "venta",
        "comercio": "venta",
        "cedio": "venta",
        "ceder": "venta",
        "trafico": "venta",
        "traficar": "venta",

        # Descubrimiento / Enterarse
        "descubrir": "descubrir",
        "descubro": "descubrir",
        "descubri": "descubrir",
        "descubrio": "descubrir",
        "enterar": "descubrir",
        "entere": "descubrir",
        "entero": "descubrir",
        "doy": "descubrir",       # de 'doy cuenta'
        "cuenta": "descubrir",    # de 'doy cuenta'
        "notar": "descubrir",
        "note": "descubrir",
        "saber": "descubrir",
        "supe": "descubrir",

        # Datos / Información personal
        "dato": "datos",
        "datos": "datos",
        "informacion": "datos",

        # Sujeto infractor / Responsable
        "empresa": "responsable",
        "empresas": "responsable",
        "compania": "responsable",
        "companias": "responsable",
        "entidad": "responsable",
        "entidades": "responsable",
        "negocio": "responsable",
        "alguien": "responsable",
        "tercero": "responsable",
        "terceros": "responsable",
        "persona": "responsable",

        # Tutela / Amparo
        "tutela": "tutela",
        "amparo": "tutela",

        # Juramento estimatorio
        "estimatorio": "juramento_estimatorio",
        "estimacion": "juramento_estimatorio",

        # Medidas cautelares
        "cautelar": "medida_cautelar",
        "cautelares": "medida_cautelar",
        "innominada": "medida_cautelar",
        "innominadas": "medida_cautelar"
    }

    # Correcciones tipográficas comunes (typos)
    TYPO_MAP: Dict[str, str] = {
        "debor": "debo",
        "devor": "debo",
        "haser": "hacer",
        "aser": "hacer",
        "qeu": "que",
        "q": "que",
        "k": "que",
        "xq": "porque",
        "vendio": "vendio",
        "empresa": "empresa"
    }

    @staticmethod
    def strip_accents(text: str) -> str:
        """Elimina tildes y diacríticos: 'vendió' -> 'vendio', 'tutela' -> 'tutela'."""
        if not text:
            return ""
        nfkd_form = unicodedata.normalize('NFKD', text)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    @classmethod
    def clean_word(cls, word: str) -> str:
        w = cls.strip_accents(word.lower().strip())
        w = re.sub(r'[^a-z0-9_]', '', w)
        if w in cls.TYPO_MAP:
            w = cls.TYPO_MAP[w]
        return w

    @classmethod
    def extract_canonical_concepts(cls, text: str) -> Set[str]:
        """
        Extrae un conjunto canónico de conceptos jurídicos normalizados.
        Ejemplo: 'que debor hacer si me doy cuenta que una empresa vendio mis datos sin permiso?'
        -> {'datos', 'descubrir', 'responsable', 'venta', 'autorizacion'}
        """
        if not text:
            return set()

        raw_words = re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+\b', text)
        canonical_tokens: Set[str] = set()

        # Detección de frases multipalabra ('doy cuenta', 'darme cuenta')
        norm_full = cls.strip_accents(text.lower())
        if "doy cuenta" in norm_full or "darme cuenta" in norm_full or "di cuenta" in norm_full:
            canonical_tokens.add("descubrir")
        if "juramento estimatorio" in norm_full:
            canonical_tokens.add("juramento_estimatorio")
        if "medida cautelar" in norm_full or "medidas cautelares" in norm_full:
            canonical_tokens.add("medida_cautelar")
        if "datos personales" in norm_full:
            canonical_tokens.add("datos")

        for w_raw in raw_words:
            w = cls.clean_word(w_raw)
            if not w or w in cls.STOPWORDS:
                continue

            # Mapear sinónimos canónicos
            if w in cls.SYNONYM_MAP:
                canonical_tokens.add(cls.SYNONYM_MAP[w])
            else:
                # Comprobación de prefijo/raíz
                matched = False
                for syn_key, syn_val in cls.SYNONYM_MAP.items():
                    if len(syn_key) >= 4 and w.startswith(syn_key[:4]):
                        canonical_tokens.add(syn_val)
                        matched = True
                        break
                if not matched and len(w) >= 3:
                    canonical_tokens.add(w)

        return canonical_tokens

    @classmethod
    def similarity(cls, text_a: str, text_b: str) -> float:
        """
        Calcula la similitud conceptual entre dos preguntas jurídicas (0.0 a 1.0).
        Combina solapamiento de conceptos canónicos con concordancia de secuencia difusa.
        """
        concepts_a = cls.extract_canonical_concepts(text_a)
        concepts_b = cls.extract_canonical_concepts(text_b)

        if not concepts_a or not concepts_b:
            return 0.0

        # Jaccard sobre conceptos canónicos
        intersection = concepts_a & concepts_b
        union = concepts_a | concepts_b
        concept_jaccard = len(intersection) / len(union) if union else 0.0

        # Si comparten conceptos nucleares críticos (ej: venta + datos + autorizacion)
        core_cluster = {"venta", "datos"}
        has_core_a = core_cluster.issubset(concepts_a)
        has_core_b = core_cluster.issubset(concepts_b)
        bonus = 0.20 if (has_core_a and has_core_b) else 0.0

        # Similitud difusa sobre textos normalizados
        norm_a = cls.strip_accents(text_a.lower())
        norm_b = cls.strip_accents(text_b.lower())
        seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()

        total_score = min(1.0, 0.70 * concept_jaccard + 0.15 * seq_ratio + bonus)
        return round(total_score, 3)
