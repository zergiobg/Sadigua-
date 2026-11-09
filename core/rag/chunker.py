import re
from typing import List, Dict, Any
from pathlib import Path

class LegalHierarchicalChunker:
    """
    Chunker especializado en textos normativos, doctrinales y jurídicos.
    En lugar de cortar texto ciegamente por longitud fija, segmenta preservando
    la jerarquía del documento: LIBRO > TÍTULO > CAPÍTULO > ARTÍCULO > PARÁGRAFO.
    """

    def __init__(self, target_chunk_size: int = 600, overlap: int = 100):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def chunk_markdown(self, text: str, source_path: str = "") -> List[Dict[str, Any]]:
        chunks = []
        filename = Path(source_path).name if source_path else "documento"

        lines = text.split("\n")
        current_h1 = ""
        current_h2 = ""
        current_h3 = ""
        current_section = ""
        current_text_buffer = []

        def flush_buffer():
            nonlocal current_text_buffer
            if not current_text_buffer:
                return
            body = "\n".join(current_text_buffer).strip()
            if len(body) > 20: # Ignorar fragmentos vacíos
                # Extraer artículos si existen
                art_match = re.search(r'((?:ART[IÍ]CULO|Art[ií]culo|Art\.)\s+\d+[\.\°\º]*)', current_section or body, re.IGNORECASE)
                articulo = art_match.group(1).strip() if art_match else ""

                header_prefix = " > ".join(filter(None, [current_h1, current_h2, current_h3, current_section]))
                full_content = f"[{header_prefix}]\n{body}" if header_prefix else body

                chunks.append({
                    "id": f"{filename}_{len(chunks)+1}",
                    "source": filename,
                    "source_path": source_path,
                    "h1": current_h1,
                    "h2": current_h2,
                    "h3": current_h3,
                    "section": current_section,
                    "articulo": articulo,
                    "content": full_content,
                    "raw_body": body
                })
            current_text_buffer = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                flush_buffer()
                current_h1 = stripped[2:].strip()
                current_h2 = ""
                current_h3 = ""
                current_section = current_h1
            elif stripped.startswith("## "):
                flush_buffer()
                current_h2 = stripped[3:].strip()
                current_h3 = ""
                current_section = current_h2
            elif stripped.startswith("### "):
                flush_buffer()
                current_h3 = stripped[4:].strip()
                current_section = current_h3
            elif stripped.startswith("#### "):
                flush_buffer()
                current_section = stripped[5:].strip()
            elif re.match(r'^(?:T[IÍ]TULO|T[ií]tulo)\s+[IVXLCDM\d]+', stripped, re.IGNORECASE):
                flush_buffer()
                current_h2 = stripped
                current_h3 = ""
                current_section = current_h2
            elif re.match(r'^(?:CAP[IÍ]TULO|Cap[ií]tulo)\s+[IVXLCDM\d]+', stripped, re.IGNORECASE):
                flush_buffer()
                current_h3 = stripped
                current_section = current_h3
            elif re.match(r'^(?:ART[IÍ]CULO|Art[ií]culo|Art\.)\s+\d+', stripped, re.IGNORECASE):
                flush_buffer()
                current_section = stripped
                current_text_buffer.append(stripped)
            else:
                if stripped:
                    current_text_buffer.append(stripped)

        flush_buffer()
        return chunks
