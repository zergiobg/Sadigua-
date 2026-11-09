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

    async def ingest_corpus(self, curator_instruction: Optional[str] = None, current_file: Optional[str] = None) -> int:
        from core.rag.mutation_engine import LexMutationEngine
        mutation_engine = LexMutationEngine()

        corpus_dir = self.cartridge_dir / "corpus"
        if not corpus_dir.exists():
            print(f"[!] Directorio de corpus no encontrado en: {corpus_dir}")
            return 0

        # Si se suministró instrucción de curaduría para un documento recién subido
        if curator_instruction and current_file:
            sample_text = ""
            for p in corpus_dir.rglob(current_file):
                if p.suffix == ".pdf":
                    sample_text = self._extract_text_from_pdf(p)[:2000]
                else:
                    sample_text = p.read_text(encoding="utf-8")[:2000]
                break

            mutation_data = await mutation_engine.interpret_curator_instruction(
                curator_instruction=curator_instruction,
                doc_filename=current_file,
                doc_text_sample=sample_text
            )
            if mutation_data and mutation_data.get("target_norm"):
                mutation_engine.record_mutation(
                    source_doc=mutation_data.get("source_doc", current_file),
                    target_norm=mutation_data.get("target_norm", ""),
                    mutation_type=mutation_data.get("mutation_type", "OVERRULING"),
                    regla_anterior=mutation_data.get("regla_anterior", ""),
                    regla_nueva=mutation_data.get("regla_nueva", ""),
                    autoridad=mutation_data.get("autoridad", "Corte Constitucional / Consejo de Estado"),
                    efectos=mutation_data.get("efectos", "Hacia el futuro (Ex nunc)"),
                    curator_notes=curator_instruction
                )
                print(f"[LexMutation] Mutación registrada con éxito: {mutation_data.get('target_norm')} -> {current_file}")

        # Obtener todas las normas y precedentes superados/derogados
        mutations = mutation_engine.list_mutations(limit=200)
        superceded_targets = {
            m["target_norm"].lower().strip(): m for m in mutations if m.get("target_norm")
        }

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
            # 3. Asignar estado de vigencia y trazabilidad a los fragmentos
            for chunk in all_chunks:
                content_lower = chunk.get("content", "").lower()
                art_lower = chunk.get("articulo", "").lower()
                source_lower = chunk.get("source", "").lower()

                matched_mutation = None
                for target_key, mut in superceded_targets.items():
                    if target_key in content_lower or target_key in art_lower or target_key in source_lower:
                        matched_mutation = mut
                        break

                if matched_mutation:
                    chunk["vigencia_status"] = "SUPERADO"
                    chunk["mutation_type"] = matched_mutation["mutation_type"]
                    chunk["superceded_by"] = matched_mutation["source_doc"]
                    chunk["regla_nueva"] = matched_mutation["regla_nueva"]
                else:
                    chunk["vigencia_status"] = "VIGENTE"

            # 4. Indexar en BM25 y persistir a disco
            self.bm25_index.index(all_chunks)
            if hasattr(self.bm25_index, "save"):
                self.bm25_index.save()
            # 5. Limpiar base vectorial previa y re-vectorizar
            self.vector_store.clear()
            await self.vector_store.add_documents(all_chunks)
            print(f"[OK] Ingesta completada con exito: {len(all_chunks)} fragmentos indexados.")

        return len(all_chunks)
