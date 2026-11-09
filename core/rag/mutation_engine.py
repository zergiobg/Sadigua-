import os
import sqlite3
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import settings
from core.engine.factory import get_llm_engine

class LexMutationEngine:
    """
    Motor de Trazabilidad, Vigencia Dinámica y Mutación de Precedentes (Overruling).
    Gestiona la base de datos relacional SQLite (data/normative_mutations.db)
    y sincroniza el Grafo de Conocimiento en el 'Cerebro Obsidiano' (vault/jurisprudencia/).
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.DATA_PATH / "normative_mutations.db")
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos SQLite soberana con la tabla de mutaciones."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS normative_mutations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_doc TEXT NOT NULL,
                    target_norm TEXT NOT NULL,
                    mutation_type TEXT NOT NULL,
                    regla_anterior TEXT NOT NULL,
                    regla_nueva TEXT NOT NULL,
                    autoridad TEXT NOT NULL,
                    fecha_mutacion TEXT NOT NULL,
                    efectos TEXT NOT NULL,
                    curator_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_target_norm ON normative_mutations (target_norm)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_doc ON normative_mutations (source_doc)
            """)
            conn.commit()
        finally:
            conn.close()

    def record_mutation(
        self,
        source_doc: str,
        target_norm: str,
        mutation_type: str,
        regla_anterior: str,
        regla_nueva: str,
        autoridad: str = "Corte Constitucional / Consejo de Estado",
        fecha_mutacion: Optional[str] = None,
        efectos: str = "Hacia el futuro (Ex nunc)",
        curator_notes: str = ""
    ) -> int:
        """
        Inserta un registro formal de mutación jurídica en la base de datos SQLite.
        """
        fecha = fecha_mutacion or datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO normative_mutations 
                (source_doc, target_norm, mutation_type, regla_anterior, regla_nueva, autoridad, fecha_mutacion, efectos, curator_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_doc,
                target_norm,
                mutation_type,
                regla_anterior,
                regla_nueva,
                autoridad,
                fecha,
                efectos,
                curator_notes
            ))
            conn.commit()
            last_id = cursor.lastrowid
        finally:
            conn.close()

        # Sincronizar en el Cerebro Obsidiano con enlaces [[wiki]] y alerta de vigencia
        try:
            from core.memory.vault_manager import ObsidianVaultManager
            vault = ObsidianVaultManager()
            vault.record_precedent_mutation({
                "source_doc": source_doc,
                "target_norm": target_norm,
                "mutation_type": mutation_type,
                "regla_anterior": regla_anterior,
                "regla_nueva": regla_nueva,
                "autoridad": autoridad,
                "fecha_mutacion": fecha,
                "efectos": efectos
            })
        except Exception as e:
            print(f"[!] Aviso: No se pudo sincronizar nota en bóveda Obsidian: {e}")

        return last_id

    def list_mutations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna el historial completo de mutaciones jurídicas registradas."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM normative_mutations ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def find_mutations_for_norm(self, norm_keyword: str) -> List[Dict[str, Any]]:
        """Busca mutaciones asociadas a un artículo, ley o sentencia por coincidencia léxica."""
        clean_kw = norm_keyword.strip().lower()
        if not clean_kw:
            return []
        
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM normative_mutations 
                WHERE LOWER(target_norm) LIKE ? 
                   OR LOWER(source_doc) LIKE ? 
                   OR LOWER(regla_anterior) LIKE ?
                   OR LOWER(regla_nueva) LIKE ?
                ORDER BY id DESC
            """, (f"%{clean_kw}%", f"%{clean_kw}%", f"%{clean_kw}%", f"%{clean_kw}%"))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    async def interpret_curator_instruction(
        self,
        curator_instruction: str,
        doc_filename: str,
        doc_text_sample: str = ""
    ) -> Dict[str, Any]:
        """
        Usa el motor LLM local para interpretar la instrucción del abogado
        y extraer la ficha estructurada de mutación normativa (Antes vs. Ahora).
        """
        if not curator_instruction:
            return {}

        prompt = (
            f"INSTRUCCIÓN DEL ABOGADO CURADOR:\n«{curator_instruction}»\n\n"
            f"DOCUMENTO SUBIDO: {doc_filename}\n"
            f"EXTRACTO DEL DOCUMENTO:\n{doc_text_sample[:1000]}\n\n"
            "INSTRUCCIÓN:\n"
            "Analiza la instrucción jurídica del abogado y extrae en formato JSON estricto "
            "la mutación normativa (qué había antes y qué hay ahora).\n"
            "Retorna ÚNICAMENTE un objeto JSON válido con estas claves exactas:\n"
            "{\n"
            '  "target_norm": "Nombre o cita exacta de la norma o sentencia afectada/superada (ej: Sentencia T-200 de 2018 o Artículo 15)",\n'
            '  "mutation_type": "OVERRULING / DEROGATORIA_EXPRESA / INEXEQUIBILIDAD / DISTINGUISHING",\n'
            '  "regla_anterior": "Resumen claro del criterio o disposición que quedó superada o derogada (¿Qué había antes?)",\n'
            '  "regla_nueva": "Resumen del nuevo criterio, regla vinculante o disposición vigente (¿Qué hay ahora?)",\n'
            '  "autoridad": "Entidad o tribunal que emite la mutación (ej: Corte Constitucional, Congreso de la República)",\n'
            '  "efectos": "Efectos temporales (ej: Inmediato / Hacia el futuro / Retroactivo)"\n'
            "}"
        )

        llm = get_llm_engine()
        try:
            raw_json = await llm.generate(
                prompt=prompt,
                system_prompt="Eres un analista dogmático de jurisprudencia y precedentes de la Corte Constitucional y Consejo de Estado de Colombia. Responde exclusivamente con JSON.",
                temperature=0.0,
                max_tokens=600
            )
            # Limpiar bloques markdown si existen
            raw_json = re.sub(r'```json\s*', '', raw_json)
            raw_json = re.sub(r'```\s*$', '', raw_json).strip()
            data = json.loads(raw_json)
            data["source_doc"] = doc_filename
            data["curator_notes"] = curator_instruction
            return data
        except Exception as e:
            # Fallback heurístico en caso de fallo de parsing
            return {
                "source_doc": doc_filename,
                "target_norm": "Jurisprudencia / Norma Previa referida en instrucción",
                "mutation_type": "OVERRULING",
                "regla_anterior": "Criterio jurisprudencial o normativo anterior",
                "regla_nueva": curator_instruction,
                "autoridad": "Corte Constitucional / Consejo de Estado",
                "efectos": "Hacia el futuro (Ex nunc)",
                "curator_notes": curator_instruction
            }
