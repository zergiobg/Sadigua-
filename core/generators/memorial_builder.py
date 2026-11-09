"""
Motor de Generación de Minutas y Memoriales Procesales para Sadigua.
Especializado en Acciones de Tutela y Derechos de Petición con Taxonomía Canónica.
Genera documentos formales listos para radicar en Markdown y formato Word (.docx).
"""

import os
import io
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

from config.settings import settings

TUTELA_TAXONOMY = {
    "SALUD_MEDICAMENTOS": {
        "nombre": "Salud: Suministro Urgente de Medicamentos (PBS / No PBS)",
        "familia": "SALUD",
        "derechos": ["Derecho a la Salud (Art. 49 C.P.)", "Derecho a la Vida Digna (Art. 11 C.P.)", "Principio de Integralidad y Continuidad"],
        "entidad_tipo": "Entidad Promotora de Salud (EPS / ADRES)",
        "fundamentos_clave": (
            "Ley Estatutaria 1751 de 2015 (Artículos 8 y 15 que prohíben la interrupción de tratamientos "
            "o la negativa por barreras administrativas o financieras). "
            "Sentencia T-760 de 2008 y Sentencia SU-508 de 2020 de la Corte Constitucional sobre la entrega oportuna "
            "e ininterrumpida de medicamentos esenciales."
        ),
        "solicita_medida_cautelar": True,
        "anexos_sugeridos": ["Copia de la fórmula médica vigente", "Historia clínica actualizada", "Radicado de solicitud ante la EPS sin respuesta o con negativa", "Cédula de ciudadanía"]
    },
    "SALUD_TRATAMIENTOS": {
        "nombre": "Salud: Autorización de Cirugía, Procedimiento o Especialista",
        "familia": "SALUD",
        "derechos": ["Derecho a la Salud (Art. 49 C.P.)", "Vida en Condiciones Dignas e Integridad Personal (Art. 11 y 12 C.P.)"],
        "entidad_tipo": "Entidad Promotora de Salud (EPS)",
        "fundamentos_clave": (
            "Ley Estatutaria 1751 de 2015 (Artículos 6, 8 y 10). "
            "Sentencia T-760 de 2008 de la Corte Constitucional (Garantía de acceso a procedimientos requeridos "
            "sin dilaciones burocráticas injustificadas que pongan en riesgo la recuperación del paciente)."
        ),
        "solicita_medida_cautelar": True,
        "anexos_sugeridos": ["Orden médica emitida por médico tratante", "Epicrisis o historia clínica", "Negativa o dilación documentada de la EPS"]
    },
    "SALUD_TRANSPORTE": {
        "nombre": "Salud: Viáticos y Transporte para Paciente y Acompañante",
        "familia": "SALUD",
        "derechos": ["Derecho a la Salud (Art. 49 C.P.)", "Mínimo Vital (Art. 1 C.P.)", "Accesibilidad Geográfica al Sistema de Salud"],
        "entidad_tipo": "Entidad Promotora de Salud (EPS / FOSYGA / ADRES)",
        "fundamentos_clave": (
            "Resolución 2292 de 2021 del Ministerio de Salud. "
            "Sentencia T-122 de 2021 y T-045 de 2022 de la Corte Constitucional (Obligación de cubrir gastos de traslado "
            "y sostenimiento cuando el paciente o su núcleo familiar carecen de recursos económicos y el servicio no se presta en el municipio de residencia)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Remisión a centro médico fuera del municipio", "Manifestación bajo juramento de insolvencia para costear transporte", "Certificado de asignación de cita médica foránea"]
    },
    "PENSION_VEJEZ": {
        "nombre": "Pensión: Mora en Reconocimiento de Pensión de Vejez / Invalidez",
        "familia": "SEGURIDAD_SOCIAL",
        "derechos": ["Derecho a la Seguridad Social (Art. 48 C.P.)", "Mínimo Vital de la Persona Mayor (Art. 46 C.P.)", "Debido Proceso Administrativo (Art. 29 C.P.)"],
        "entidad_tipo": "Colpensiones o Fondo Privado de Pensiones (AFP)",
        "fundamentos_clave": (
            "Artículo 48 de la Constitución Política y Ley 100 de 1993. "
            "Ley 700 de 2001 (Término improrrogable de cuatro (4) meses para reconocer la pensión). "
            "Sentencia T-063 de 2018 y SU-140 de 2019 de la Corte Constitucional (Procedencia de la tutela para proteger el mínimo vital ante la inactividad pensional)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Copia de la solicitud pensional radicada con fecha legible", "Historia laboral con semanas cotizadas", "Copia del documento de identidad"]
    },
    "PENSION_INCAPACIDADES": {
        "nombre": "Pensión: Pago de Incapacidades Continuas Superiores a 180 Días",
        "familia": "SEGURIDAD_SOCIAL",
        "derechos": ["Mínimo Vital y Móvil (Art. 53 C.P.)", "Seguridad Social (Art. 48 C.P.)", "Vida Digna"],
        "entidad_tipo": "Fondo de Pensiones (AFP) y EPS solidariamente",
        "fundamentos_clave": (
            "Artículo 142 del Decreto Ley 019 de 2012 y Ley 100 de 1993. "
            "Sentencia T-200 de 2017 y T-144 de 2016 de la Corte Constitucional (Subsidio de incapacidad como sustituto salarial indispensable para la subsistencia digna del trabajador enfermo)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Incapacidades médicas consecutivas superiores al día 180", "Concepto de rehabilitación favorable/desfavorable", "Comprobantes de no pago"]
    },
    "PETICION_SILENCIO": {
        "nombre": "Derecho de Petición: Violación por Silencio Administrativo",
        "familia": "DERECHO_PETICION",
        "derechos": ["Derecho Fundamental de Petición (Art. 23 C.P.)", "Acceso a la Información Pública"],
        "entidad_tipo": "Cualquier autoridad pública o particular prestador de servicios",
        "fundamentos_clave": (
            "Artículo 23 de la Constitución Política de Colombia. "
            "Ley Estatutaria 1755 de 2015 (Código de Procedimiento Administrativo y de lo Contencioso Administrativo). "
            "Sentencia C-951 de 2014 y T-149 de 2013 (El núcleo esencial del derecho de petición comprende la pronta resolución, respuesta de fondo, clara, precisa, congruente y su oportuna notificación)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Copia de la petición radicada con sello o constancia de radicación digital", "Pantallazo o constancia de vencimiento de términos"]
    },
    "LABORAL_FUERO_SALUD": {
        "nombre": "Laboral: Estabilidad Reforzada por Estado de Salud / Discapacidad",
        "familia": "LABORAL",
        "derechos": ["Derecho al Trabajo (Art. 25 C.P.)", "Estabilidad Laboral Reforzada (Art. 53 C.P.)", "Igualdad y No Discriminación (Art. 13 C.P.)"],
        "entidad_tipo": "Empresa Empleadora Pública o Privada",
        "fundamentos_clave": (
            "Artículo 26 de la Ley 361 de 1997. "
            "Sentencia de Unificación SU-049 de 2017 de la Corte Constitucional (Presunción de despido discriminatorio y nulidad del despido sin autorización previa del Ministerio del Trabajo para personas en situación de debilidad manifiesta)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Contrato de trabajo o certificado laboral", "Dictamen médico o incapacidades vigentes a la fecha del despido", "Carta de despido o terminación"]
    },
    "LABORAL_FUERO_MATERNIDAD": {
        "nombre": "Laboral: Fuero de Maternidad y Lactancia",
        "familia": "LABORAL",
        "derechos": ["Protección a la Mujer Embarazada (Art. 43 C.P.)", "Derecho al Trabajo (Art. 25 C.P.)", "Mínimo Vital del Recién Nacido"],
        "entidad_tipo": "Empleador Público o Privado",
        "fundamentos_clave": (
            "Artículos 239 y 240 del Código Sustantivo del Trabajo. "
            "Sentencia de Unificación SU-070 de 2013 y SU-075 de 2018 (Protección reforzada incondicional independientemente de la modalidad contractual de vinculación)."
        ),
        "solicita_medida_cautelar": True,
        "anexos_sugeridos": ["Prueba de embarazo o certificado médico de gestación", "Comunicación del estado de gravidez al empleador", "Carta de despido"]
    },
    "HABEAS_DATA_CADUCIDAD": {
        "nombre": "Habeas Data: Caducidad de Reporte Negativo en Centrales de Riesgo",
        "familia": "HABEAS_DATA",
        "derechos": ["Derecho al Hábeas Data y Buen Nombre (Art. 15 C.P.)", "Derecho al Olvido"],
        "entidad_tipo": "Datacrédito (Experian), TransUnion (CIFIN) y Entidad Financiera Fuente",
        "fundamentos_clave": (
            "Ley Estatutaria 1266 de 2008 y Ley Estatutaria 2157 de 2021 (Ley de Borrón y Cuenta Nueva). "
            "Sentencia C-282 de 2021 de la Corte Constitucional (Límites temporales estrictos a la permanencia de la información financiera negativa tras la extinción de la obligación)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Paz y salvo de la obligación cancelada", "Petición de retiro radicada ante la central de riesgo", "Reporte de la central con fecha de registro"]
    },
    "DEBIDO_PROCESO_JUDICIAL": {
        "nombre": "Debido Proceso: Tutela contra Providencia Judicial (Vía de Hecho)",
        "familia": "DEBIDO_PROCESO",
        "derechos": ["Derecho al Debido Proceso (Art. 29 C.P.)", "Acceso a la Administración de Justicia (Art. 229 C.P.)"],
        "entidad_tipo": "Juzgado o Tribunal Judicial Accionado",
        "fundamentos_clave": (
            "Artículo 29 de la Constitución Política de Colombia. "
            "Sentencia C-590 de 2005 y Sentencia SU-116 de 2018 de la Corte Constitucional (Requisitos generales de procedibilidad: inmediatez y subsidiariedad; y causales específicas: defecto fáctico, sustantivo, procedimental absoluto o desconocimiento del precedente)."
        ),
        "solicita_medida_cautelar": False,
        "anexos_sugeridos": ["Copia de la providencia judicial impugnada", "Recursos ordinarios agotados en el proceso", "Constancia de notificación"]
    }
}

PETICION_TAXONOMY = {
    "PETICION_DOCUMENTOS": {
        "nombre": "Solicitud de Información y Copias de Documentos (10 días)",
        "plazo_legal": "Diez (10) días hábiles",
        "fundamento_legal": "Artículo 14, Numeral 1 de la Ley Estatutaria 1755 de 2015. Artículo 74 de la Constitución Política.",
        "consecuencia_silencio": "Si no se responde en 10 días, se entenderá aceptada la solicitud y las copias deberán entregarse dentro de los 3 días siguientes (Art. 14 num 1 Ley 1755)."
    },
    "PETICION_INTERES_GENERAL": {
        "nombre": "Petición de Interés General o Particular (15 días)",
        "plazo_legal": "Quince (15) días hábiles",
        "fundamento_legal": "Artículo 14, Inciso 1 de la Ley Estatutaria 1755 de 2015. Artículo 23 de la Constitución Política.",
        "consecuencia_silencio": "Falta disciplinaria sancionable para el funcionario público y procedencia inmediata de la Acción de Tutela por vulneración del derecho de petición."
    },
    "PETICION_CONSULTA": {
        "nombre": "Consulta de Conceptos Jurídicos o Técnicos (30 días)",
        "plazo_legal": "Treinta (30) días hábiles",
        "fundamento_legal": "Artículo 14, Numeral 2 de la Ley Estatutaria 1755 de 2015.",
        "consecuencia_silencio": "Obligación de respuesta motivada. El silencio habilita la queja disciplinaria ante la Procuraduría o Personería."
    }
}


class LegalMemorialBuilder:
    """
    Generador Soberano de Minutas y Memoriales Procesales.
    Produce documentos con estructura formal judicial en Markdown y Word (.docx).
    """

    def __init__(self):
        pass

    def get_taxonomy(self) -> Dict[str, Any]:
        """Devuelve el árbol taxonómico para el frontend."""
        return {
            "tutelas": TUTELA_TAXONOMY,
            "peticiones": PETICION_TAXONOMY
        }

    def generate_tutela_markdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera el texto formal de una Acción de Tutela en Markdown."""
        cat_id = data.get("categoria_id", "SALUD_MEDICAMENTOS")
        tax = TUTELA_TAXONOMY.get(cat_id, TUTELA_TAXONOMY["SALUD_MEDICAMENTOS"])

        ciudad = data.get("ciudad", "Bogotá D.C.")
        fecha_actual = datetime.now().strftime("%d de %B de %Y")
        accionante = data.get("accionante_nombre", "[NOMBRE DEL ACCIONANTE]").upper()
        cc_accionante = data.get("accionante_identificacion", "[C.C. No. XXXXXXXXX]")
        correo_accionante = data.get("accionante_correo", "[CORREO ELECTRÓNICO]")
        telefono_accionante = data.get("accionante_telefono", "[TELÉFONO DE CONTACTO]")
        
        accionado = data.get("accionado_nombre", "[ENTIDAD ACCIONADA]").upper()
        nit_accionado = data.get("accionado_nit", "")
        correo_accionado = data.get("accionado_correo", "[CORREO NOTIFICACIONES ACCIONADO]")

        hechos = data.get("hechos", "").strip()
        if not hechos:
            hechos = (
                "1. En mi condición de ciudadano y usuario adscrito a la entidad accionada, "
                "he venido requiriendo de forma oportuna la atención debida conforme a mi situación.\n"
                "2. La entidad accionada ha omitido de manera injustificada cumplir con sus deberes legales y constitucionales, "
                "generando una afectación directa y grave a mis derechos fundamentales.\n"
                "3. A la fecha de radicación de este amparo constitucional, persiste la vulneración sin que exista otro medio de defensa expedito y eficaz."
            )
        else:
            # Formatear hechos en párrafos numerados si no lo están
            lineas = [l.strip() for l in hechos.split("\n") if l.strip()]
            hechos_formateados = []
            for i, l in enumerate(lineas):
                if re.match(r'^\d+\.', l):
                    hechos_formateados.append(l)
                else:
                    hechos_formateados.append(f"{i+1}. {l}")
            hechos = "\n\n".join(hechos_formateados)

        pretensiones_custom = data.get("pretensiones", "").strip()
        if not pretensiones_custom:
            pretensiones = (
                f"**PRIMERA:** TUTELAR de manera inmediata e incondicional los derechos fundamentales a {', '.join(tax['derechos'])}, "
                f"vulnerados por {accionado} a favor de {accionante}.\n\n"
                f"**SEGUNDA:** ORDENAR al representante legal de {accionado} que, dentro del término perentorio de cuarenta y ocho (48) horas siguientes a la notificación del fallo, "
                f"proceda a autorizar, gestionar y hacer efectiva la prestación requerida para mitigar la vulneración denunciada.\n\n"
                f"**TERCERA:** PREVENIR a la accionada para que en el futuro se abstenga de incurrir en conductas omisivas similares."
            )
        else:
            pretensiones = pretensiones_custom

        medida_cautelar_solicitada = data.get("solicitar_medida_cautelar", tax.get("solicita_medida_cautelar", False))
        medida_bloque = ""
        if medida_cautelar_solicitada:
            medida_bloque = (
                "### MEDIDA CAUTELAR PROVISIONAL DE PROTECCIÓN INMEDIATA (ARTÍCULO 7° DEL DECRETO 2591 DE 1991)\n\n"
                "De conformidad con el Artículo 7° del Decreto 2591 de 1991, solicito muy respetuosamente a su Despacho "
                "decretar **MEDIDA PROVISIONAL INMEDIATA** ordenando a la entidad accionada que, en el término de veinticuatro (24) horas, "
                "garantice la entrega o autorización provisional de lo reclamado, habida cuenta del inminente riesgo de consumación "
                "de un perjuicio irremediable para la vida, la salud o el mínimo vital del accionante.\n\n"
                "---\n"
            )

        derechos_str = "\n".join([f"- **{d}**" for d in tax["derechos"]])
        anexos_list = tax["anexos_sugeridos"] + [f"Cédula de ciudadanía de {accionante}"]
        anexos_str = "\n".join([f"{i+1}. {a}" for i, a in enumerate(anexos_list)])

        md_content = f"""# ACCIÓN DE TUTELA PARA LA PROTECCIÓN DE DERECHOS FUNDAMENTALES

**Señor(a):**  
**JUEZ CONSTITUCIONAL DE REPARTO**  
**E. S. D.**  

| Referencia Procesal | Datos de Radicación |
| :--- | :--- |
| **Acción Constitucional:** | Acción de Tutela (Artículo 86 de la C.P. y Decreto 2591 de 1991) |
| **Accionante:** | **{accionante}** (C.C. {cc_accionante}) |
| **Accionado:** | **{accionado}** {f'(NIT: {nit_accionado})' if nit_accionado else ''} |
| **Derechos Invocados:** | {', '.join(tax['derechos'])} |
| **Asunto / Taxonomía:** | {tax['nombre']} |
| **Lugar y Fecha:** | {ciudad}, {fecha_actual} |

---

Yo, **{accionante}**, mayor de edad, identificado(a) con la cédula de ciudadanía número **{cc_accionante}**, domiciliado(a) y residente en la ciudad de **{ciudad}**, obrando en nombre propio, acudo muy respetuosamente ante su Despacho Judicial con el fin de formular **ACCIÓN DE TUTELA** en contra de **{accionado}**, para que se me amparen y restablezcan de forma urgente los siguientes derechos fundamentales:

### I. DERECHOS FUNDAMENTALES VULNERADOS
{derechos_str}

---

{medida_bloque}

### II. HECHOS FÁCTICOS
Fundamento la presente solicitud de amparo en los siguientes hechos claros y cronológicos:

{hechos}

---

### III. FUNDAMENTOS DE DERECHO Y PRECEDENTE CONSTITUCIONAL VINCULANTE
1. **Rango Constitucional (Artículo 86 C.P.):** Toda persona tendrá acción de tutela para reclamar ante los jueces, en todo momento y lugar, mediante un procedimiento preferente y sumario, por sí misma o por quien actúe a su nombre, la protección inmediata de sus derechos constitucionales fundamentales.
2. **Marco Estatutario y Jurisprudencial de la Materia:**  
   {tax['fundamentos_clave']}
3. **Inmediatez y Subsidiariedad:** La presente acción satisface cabalmente el requisito de subsidiariedad al no existir otro medio de defensa judicial con la misma eficacia sumaria para evitar un perjuicio irremediable, así como el principio de inmediatez al encontrarse la vulneración actual y vigente en el tiempo.

---

### IV. PRETENSIONES
Con fundamento en los hechos y el derecho expuesto, solicito al señor Juez Constitucional:

{pretensiones}

---

### V. JURAMENTO (ARTÍCULO 37 DEL DECRETO 2591 DE 1991)
Bajo la gravedad del juramento, que se entiende prestado con la presentación de este escrito, manifiesto que no he instaurado otra acción de tutela ante ninguna autoridad judicial por los mismos hechos y derechos aquí invocados.

---

### VI. PRUEBAS Y ANEXOS DOCUMENTALES
Ruego a su Despacho tener como pruebas y decretar las siguientes:
{anexos_str}

---

### VII. NOTIFICACIONES
- **Accionante:** Recibiré notificaciones judiciales en el correo electrónico: `{correo_accionante}` | Teléfono: `{telefono_accionante}` | Dirección: `{ciudad}`.
- **Accionada:** La entidad {accionado} recibirá notificaciones en el correo institucional: `{correo_accionado}`.

Atentamente,

**{accionante}**  
C.C. {cc_accionante}  
Accionante en Tutela  
"""
        doc_id = f"tutela_{cat_id.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "doc_id": doc_id,
            "tipo": "TUTELA",
            "categoria_id": cat_id,
            "categoria_nombre": tax["nombre"],
            "familia": tax["familia"],
            "markdown": md_content,
            "entidad_accionada": accionado,
            "accionante": accionante,
            "created_at": datetime.now().isoformat()
        }

    def generate_peticion_markdown(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera el texto formal de un Derecho de Petición en Markdown."""
        cat_id = data.get("categoria_id", "PETICION_DOCUMENTOS")
        tax = PETICION_TAXONOMY.get(cat_id, PETICION_TAXONOMY["PETICION_DOCUMENTOS"])

        ciudad = data.get("ciudad", "Bogotá D.C.")
        fecha_actual = datetime.now().strftime("%d de %B de %Y")
        peticionario = data.get("accionante_nombre", "[NOMBRE DEL PETICIONARIO]").upper()
        cc_peticionario = data.get("accionante_identificacion", "[C.C. No. XXXXXXXXX]")
        correo_peticionario = data.get("accionante_correo", "[CORREO ELECTRÓNICO]")
        telefono_peticionario = data.get("accionante_telefono", "[TELÉFONO DE CONTACTO]")

        destinatario = data.get("accionado_nombre", "[ENTIDAD U ORGANISMO DESTINATARIO]").upper()
        correo_destinatario = data.get("accionado_correo", "[CORREO DE CONTACTO / PQR]")

        hechos = data.get("hechos", "").strip()
        if not hechos:
            hechos = (
                "1. En ejercicio de mis facultades legales y constitucionales, acudo ante su entidad con el fin de elevar solicitud formal.\n"
                "2. A la fecha requiero información clara y oportuna para el ejercicio pleno de mis derechos."
            )

        solicitud = data.get("pretensiones", "").strip()
        if not solicitud:
            solicitud = (
                "1. Solicito se me expida y remita copia completa y legible de los documentos e informaciones solicitadas.\n"
                "2. Se me informe de manera clara, precisa y de fondo el estado actual de la actuación administrativa."
            )

        md_content = f"""# DERECHO DE PETICIÓN FORMAL (ARTÍCULO 23 C.P. Y LEY 1755 DE 2015)

**{ciudad}**, {fecha_actual}

**Señores:**  
**{destinatario}**  
**Oficina de Peticiones, Quejas, Reclamos y Atención al Ciudadano**  
Correo de Radicación: `{correo_destinatario}`  
**E. S. D.**  

| Referencia | Formulación de Petición |
| :--- | :--- |
| **Peticionario:** | **{peticionario}** (C.C. {cc_peticionario}) |
| **Modalidad:** | {tax['nombre']} |
| **Plazo Legal Máximo:** | **{tax['plazo_legal']}** (Ley Estatutaria 1755 de 2015) |
| **Asunto:** | Solicitud formal en ejercicio del Derecho Fundamental de Petición |

---

Yo, **{peticionario}**, identificado(a) con cédula de ciudadanía No. **{cc_peticionario}**, actuando en nombre propio y en ejercicio del Derecho Fundamental de Petición consagrado en el **Artículo 23 de la Constitución Política de Colombia** y regulado por la **Ley Estatutaria 1755 de 2015**, me dirijo a ustedes para formular las siguientes peticiones:

### I. OBJETO DE LA PETICIÓN (PETITUM)
{solicitud}

---

### II. HECHOS EN QUE SE FUNDA
{hechos}

---

### III. FUNDAMENTOS JURÍDICOS Y TÉRMINOS LEGALES DE RESPUESTA
1. **Artículo 23 de la Constitución Política:** Toda persona tiene derecho a presentar peticiones respetuosas a las autoridades por motivos de interés general o particular y a obtener pronta resolución.
2. **Ley Estatutaria 1755 de 2015:** {tax['fundamento_legal']}
3. **Término Perentorio:** El término legal e improrrogable para responder la presente solicitud es de **{tax['plazo_legal']}**.
4. **Advertencia de Silencio:** {tax['consecuencia_silencio']}

---

### IV. ANEXOS DOCUMENTALES
1. Copia de la cédula de ciudadanía del peticionario.
2. Soportes adicionales adjuntos a este memorial.

---

### V. NOTIFICACIONES
Solicito formalmente que la respuesta de fondo sea notificada exclusivamente a la siguiente dirección electrónica:
- Correo Electrónico: `{correo_peticionario}`
- Teléfono de Contacto: `{telefono_peticionario}`
- Dirección física: `{ciudad}`

Respetuosamente,

**{peticionario}**  
C.C. {cc_peticionario}  
Peticionario(a)  
"""
        doc_id = f"peticion_{cat_id.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "doc_id": doc_id,
            "tipo": "DERECHO_PETICION",
            "categoria_id": cat_id,
            "categoria_nombre": tax["nombre"],
            "plazo_legal": tax["plazo_legal"],
            "markdown": md_content,
            "entidad_accionada": destinatario,
            "accionante": peticionario,
            "created_at": datetime.now().isoformat()
        }

    def export_to_docx(self, memorial_data: Dict[str, Any]) -> io.BytesIO:
        """
        Convierte una minuta generada a un documento Word (.docx) formal
        con formato tipográfico judicial estándar (Márgenes 3cm, Calibri/Arial 11-12pt,
        interlineado 1.15, títulos en negrita con espaciado profesional).
        """
        doc = Document()

        # Configurar márgenes de página (2.54 cm / 1 pulgada estándar formal)
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.1)
            section.right_margin = Inches(1.0)

        # Configurar estilo Normal
        style = doc.styles['Normal']
        style.font.name = 'Calibri'
        style.font.size = Pt(11.5)
        style.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)
        style.paragraph_format.line_spacing = 1.2
        style.paragraph_format.space_after = Pt(6)

        md_text = memorial_data.get("markdown", "")
        lines = md_text.splitlines()

        in_table = False
        table_rows = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Saltar separadores markdown ---
            if stripped == "---":
                continue

            # Títulos Markdown
            if stripped.startswith("# "):
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(stripped[2:])
                run.bold = True
                run.font.size = Pt(15)
                run.font.color.rgb = RGBColor(0x01, 0x1C, 0x38)
                p.paragraph_format.space_after = Pt(12)
                continue

            if stripped.startswith("## "):
                p = doc.add_paragraph()
                run = p.add_run(stripped[3:])
                run.bold = True
                run.font.size = Pt(13)
                run.font.color.rgb = RGBColor(0x08, 0x33, 0x58)
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(6)
                continue

            if stripped.startswith("### "):
                p = doc.add_paragraph()
                run = p.add_run(stripped[4:])
                run.bold = True
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0x0C, 0x4A, 0x6E)
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(4)
                continue

            # Tablas Markdown
            if stripped.startswith("|") and stripped.endswith("|"):
                if ":---" in stripped or "---:" in stripped:
                    continue  # Fila separadora de tabla
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if not in_table:
                    in_table = True
                    table_rows = [cells]
                else:
                    table_rows.append(cells)
                continue
            else:
                if in_table and table_rows:
                    # Renderizar tabla acumulada
                    t = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
                    t.style = 'Light Shading Accent 1'
                    for r_idx, row in enumerate(table_rows):
                        for c_idx, cell_text in enumerate(row):
                            clean_cell = cell_text.replace("**", "").replace("*", "")
                            t.cell(r_idx, c_idx).text = clean_cell
                    p_spacer = doc.add_paragraph()
                    p_spacer.paragraph_format.space_after = Pt(4)
                    in_table = False
                    table_rows = []

            # Listas no numeradas
            if stripped.startswith("- ") or stripped.startswith("* "):
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_after = Pt(3)
                self._add_formatted_runs(p, stripped[2:])
                continue

            # Párrafos normales
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            self._add_formatted_runs(p, stripped)

        # Si quedó tabla pendiente al final
        if in_table and table_rows:
            t = doc.add_table(rows=len(table_rows), cols=len(table_rows[0]))
            t.style = 'Light Shading Accent 1'
            for r_idx, row in enumerate(table_rows):
                for c_idx, cell_text in enumerate(row):
                    clean_cell = cell_text.replace("**", "").replace("*", "")
                    t.cell(r_idx, c_idx).text = clean_cell

        stream = io.BytesIO()
        doc.save(stream)
        stream.seek(0)
        return stream

    def _add_formatted_runs(self, paragraph, text: str):
        """Parsea negritas **texto** y agrega runs formateados al párrafo docx."""
        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            elif part.startswith('`') and part.endswith('`'):
                run = paragraph.add_run(part[1:-1])
                run.font.name = 'Consolas'
                run.font.size = Pt(10)
            else:
                paragraph.add_run(part)

    def save_to_vault(self, memorial_data: Dict[str, Any]) -> str:
        """Guarda la minuta tipificada en la Bóveda de Obsidian."""
        tipo = memorial_data.get("tipo", "TUTELA").lower()
        cat_id = memorial_data.get("categoria_id", "general").lower()
        doc_id = memorial_data.get("doc_id", "minuta")

        folder_name = "tutelas" if "tutela" in tipo else "peticiones"
        target_dir = settings.VAULT_PATH / "minutas" / folder_name / cat_id
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / f"{doc_id}.md"

        frontmatter = (
            f"---\n"
            f"id: \"{doc_id}\"\n"
            f"tipo_accion: \"{memorial_data.get('tipo')}\"\n"
            f"categoria: \"{cat_id}\"\n"
            f"categoria_nombre: \"{memorial_data.get('categoria_nombre')}\"\n"
            f"accionante: \"{memorial_data.get('accionante')}\"\n"
            f"entidad_accionada: \"{memorial_data.get('entidad_accionada')}\"\n"
            f"created_at: \"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\"\n"
            f"tags: [\"minuta\", \"{folder_name}\", \"{cat_id}\"]\n"
            f"---\n\n"
        )

        full_content = frontmatter + memorial_data.get("markdown", "")
        target_file.write_text(full_content, encoding="utf-8")
        return str(target_file)
