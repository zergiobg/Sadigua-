import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.rag.chunker import LegalHierarchicalChunker
from core.rag.bm25_index import PureBM25Index
from core.rag.vector_store import LocalVectorStore
from config.settings import settings

class IngestionPipeline:
    """
    Pipeline de Ingesta y Curaduría Documental para Cartuchos de Sadigua.
    Segmenta, indexa léxicamente (BM25) y vectoriza el corpus del cartucho activo.
    Soporta Markdown (.md), Texto plano (.txt) y Documentos PDF (.pdf).
    """

    def __init__(
        self,
        cartridge_name: Optional[str] = None,
        vector_store: Optional[LocalVectorStore] = None,
        bm25_index: Optional[PureBM25Index] = None
    ):
        self.cartridge_name = cartridge_name or settings.ACTIVE_CARTRIDGE
        self.cartridge_dir = settings.CARTRIDGES_PATH / self.cartridge_name
        self.vector_store = vector_store or LocalVectorStore()
        self.bm25_index = bm25_index or PureBM25Index()
        self.chunker = LegalHierarchicalChunker()

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extrae texto de archivos PDF usando pypdf."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(pdf_path))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(f"\n### PÁGINA {i+1}\n{text}")
            return "\n".join(pages_text)
        except Exception as e:
            print(f"[!] Error extrayendo texto del PDF {pdf_path.name}: {e}")
            return ""

    async def ingest_corpus(self) -> int:
        corpus_dir = self.cartridge_dir / "corpus"
        if not corpus_dir.exists():
            print(f"[!] Directorio de corpus no encontrado en: {corpus_dir}")
            return 0

        all_chunks: List[Dict[str, Any]] = []

        # 1. Procesar archivos Markdown y Texto
        for ext in ["*.md", "*.txt"]:
            for filepath in corpus_dir.rglob(ext):
                try:
                    text = filepath.read_text(encoding="utf-8")
                    chunks = self.chunker.chunk_markdown(text, source_path=str(filepath))
                    all_chunks.extend(chunks)
                    print(f"[*] Procesado texto: {filepath.name} -> {len(chunks)} fragmentos.")
                except Exception as e:
                    print(f"[!] Error leyendo {filepath.name}: {e}")

        # 2. Procesar archivos PDF
        for filepath in corpus_dir.rglob("*.pdf"):
            try:
                extracted_text = self._extract_text_from_pdf(filepath)
                if extracted_text:
                    chunks = self.chunker.chunk_markdown(extracted_text, source_path=str(filepath))
                    all_chunks.extend(chunks)
                    print(f"[*] Procesado PDF: {filepath.name} -> {len(chunks)} fragmentos.")
            except Exception as e:
                print(f"[!] Error procesando PDF {filepath.name}: {e}")

        if all_chunks:
            # 1. Indexar en BM25
            self.bm25_index.index(all_chunks)
            # 2. Limpiar base vectorial previa y re-vectorizar
            self.vector_store.clear()
            await self.vector_store.add_documents(all_chunks)
            print(f"[OK] Ingesta completada con exito: {len(all_chunks)} fragmentos indexados.")

        return len(all_chunks)
