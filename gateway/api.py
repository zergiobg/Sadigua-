import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config.settings import settings
from core.engine.factory import get_llm_engine
from core.rag.bm25_index import PureBM25Index
from core.rag.vector_store import LocalVectorStore
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import PrecisionReranker
from core.rag.ingest import IngestionPipeline
from core.memory.vault_manager import ObsidianVaultManager
from core.agents.orchestrator import SadiguaOrchestrator
from core.cartridges.manager import CartridgeManager
from gateway.anonymizer import PIIAnonymizer

app = FastAPI(
    title="SADIGUA - Shell Soberano de Inteligencia Artificial",
    version="1.0.0",
    description="Motor desacoplado y RAG anti-alucinaciones con memoria persistente Obsidian."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialización de componentes del sistema
cartridge_manager = CartridgeManager()
vault_manager = ObsidianVaultManager()
bm25_index = PureBM25Index()
vector_store = LocalVectorStore()
retriever = HybridRetriever(bm25_index=bm25_index, vector_store=vector_store)
reranker = PrecisionReranker()

orchestrator = SadiguaOrchestrator(
    cartridge_name=settings.ACTIVE_CARTRIDGE,
    llm_engine=get_llm_engine(),
    retriever=retriever,
    reranker=reranker,
    vault_manager=vault_manager
)

# Modelos Pydantic para peticiones
class ChatRequest(BaseModel):
    message: str = Field(..., description="Consulta del usuario")
    anonymize: bool = Field(default=True, description="Enmascarar datos personales (Ley 1581)")

class SwitchCartridgeRequest(BaseModel):
    cartridge_id: str = Field(..., description="ID del cartucho a activar")

class ConfigUpdateRequest(BaseModel):
    llm_provider: str = Field(..., description="'gemini' o 'local'")
    cloud_egress_enabled: Optional[bool] = Field(default=None, description="Compuerta de Soberanía para permitir salida a nube")
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    local_base_url: Optional[str] = None
    local_model: Optional[str] = None

class VaultNoteCreateRequest(BaseModel):
    category: str
    note_id: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None

# -------------------------------------------------------------
# EVENTO DE INICIO
# -------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    # Ingestar corpus inicial
    pipeline = IngestionPipeline(
        cartridge_name=settings.ACTIVE_CARTRIDGE,
        vector_store=vector_store,
        bm25_index=bm25_index
    )
    count = await pipeline.ingest_corpus()
    print(f"[Sadigua] Sistema en línea. Cartucho activo: '{settings.ACTIVE_CARTRIDGE}' con {count} fragmentos cargados.")

# -------------------------------------------------------------
# ENDPOINTS DE ESTADO Y CONFIGURACIÓN
# -------------------------------------------------------------
@app.get("/api/system/status")
def get_system_status():
    from core.hardware.detector import HardwareProfiler
    hw = HardwareProfiler.profile()
    return {
        "status": "online",
        "provider": settings.LLM_PROVIDER,
        "cloud_egress_enabled": settings.CLOUD_EGRESS_ENABLED,
        "active_cartridge": settings.ACTIVE_CARTRIDGE,
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")),
        "local_model": settings.LOCAL_MODEL,
        "local_base_url": settings.LOCAL_BASE_URL,
        "vault_path": str(settings.VAULT_PATH),
        "indexed_chunks": bm25_index.N,
        "hardware_info": hw
    }

@app.get("/api/system/hardware")
def get_hardware_profile():
    from core.hardware.detector import HardwareProfiler
    return HardwareProfiler.profile()

@app.post("/api/system/config")
def update_system_config(req: ConfigUpdateRequest):
    global orchestrator
    if req.llm_provider not in ["gemini", "local"]:
        raise HTTPException(status_code=400, detail="Proveedor inválido. Use 'gemini' o 'local'.")

    if req.cloud_egress_enabled is not None:
        settings.CLOUD_EGRESS_ENABLED = req.cloud_egress_enabled

    settings.LLM_PROVIDER = req.llm_provider
    if req.gemini_api_key is not None:
        settings.GEMINI_API_KEY = req.gemini_api_key
        os.environ["GEMINI_API_KEY"] = req.gemini_api_key
    if req.gemini_model:
        settings.GEMINI_MODEL = req.gemini_model
    if req.local_base_url:
        settings.LOCAL_BASE_URL = req.local_base_url
    if req.local_model:
        settings.LOCAL_MODEL = req.local_model

    # Reiniciar motor en el orquestador verificando compuerta
    try:
        orchestrator.llm = get_llm_engine(settings.LLM_PROVIDER)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))

    return {"message": "Configuración actualizada con éxito", "status": get_system_status()}

# -------------------------------------------------------------
# ENDPOINTS DE CHAT & COGNICIÓN
# -------------------------------------------------------------
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    user_query = request.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    mapping = {}
    if request.anonymize:
        user_query, mapping = PIIAnonymizer.mask(user_query)

    result = await orchestrator.answer(user_query)

    if request.anonymize and mapping:
        result["answer"] = PIIAnonymizer.unmask(result["answer"], mapping)

    return result

# -------------------------------------------------------------
# ENDPOINTS DE CARTUCHOS & DOCUMENTOS
# -------------------------------------------------------------
@app.get("/api/cartridges")
def list_cartridges():
    return cartridge_manager.list_cartridges()

@app.post("/api/cartridges/switch")
async def switch_cartridge(req: SwitchCartridgeRequest):
    global orchestrator
    success = cartridge_manager.switch_cartridge(req.cartridge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cartucho no encontrado.")

    # Re-inicializar orquestador con el nuevo cartucho
    pipeline = IngestionPipeline(
        cartridge_name=settings.ACTIVE_CARTRIDGE,
        vector_store=vector_store,
        bm25_index=bm25_index
    )
    count = await pipeline.ingest_corpus()

    orchestrator = SadiguaOrchestrator(
        cartridge_name=settings.ACTIVE_CARTRIDGE,
        llm_engine=get_llm_engine(),
        retriever=retriever,
        reranker=reranker,
        vault_manager=vault_manager
    )

    return {
        "message": f"Cartucho cambiado exitosamente a '{settings.ACTIVE_CARTRIDGE}'",
        "indexed_chunks": count
    }

@app.get("/api/documents")
def list_cartridge_documents(cartridge_id: Optional[str] = None):
    return cartridge_manager.get_cartridge_documents(cartridge_id)

@app.get("/api/index/stats")
async def get_index_stats():
    """Retorna las métricas del motor de indexación y vectorización."""
    if len(bm25_index.corpus) == 0:
        pipeline = IngestionPipeline(
            cartridge_name=settings.ACTIVE_CARTRIDGE,
            vector_store=vector_store,
            bm25_index=bm25_index
        )
        await pipeline.ingest_corpus()

    total_chunks = len(bm25_index.corpus)
    vocab_size = len(bm25_index.doc_freqs)
    avg_len = round(bm25_index.avg_doc_len, 1) if hasattr(bm25_index, 'avg_doc_len') else 0
    return {
        "total_chunks": total_chunks,
        "vocab_size": vocab_size,
        "avg_chunk_tokens": avg_len,
        "active_cartridge": settings.ACTIVE_CARTRIDGE,
        "vector_count": len(vector_store.documents),
        "indexing_pipeline": {
            "chunker": "LegalHierarchicalChunker",
            "lexical_engine": "BM25 Okapi (k1=1.5, b=0.75)",
            "vector_engine": "Dense Embeddings + Cosine Similarity",
            "fusion": "Reciprocal Rank Fusion (RRF k=60)",
            "reranker": "Precision Cross-Encoder Heuristic"
        }
    }

@app.get("/api/index/chunks")
async def get_indexed_chunks(search: Optional[str] = None, source: Optional[str] = None):
    """Permite auditar e inspeccionar exactamente qué fragmentos y artículos están en memoria."""
    if len(bm25_index.corpus) == 0:
        pipeline = IngestionPipeline(
            cartridge_name=settings.ACTIVE_CARTRIDGE,
            vector_store=vector_store,
            bm25_index=bm25_index
        )
        await pipeline.ingest_corpus()

    results = []
    for doc in bm25_index.corpus:
        doc_source = doc.get("source", "")
        doc_content = doc.get("content", "")
        doc_art = doc.get("articulo", "") or doc.get("section", "")

        # Filtrar por fuente si aplica
        if source and source.lower() not in doc_source.lower():
            continue

        # Filtrar por búsqueda si aplica
        if search:
            q = search.lower()
            if q not in doc_content.lower() and q not in doc_art.lower() and q not in doc_source.lower():
                continue

        results.append({
            "id": doc.get("id"),
            "source": doc_source,
            "section": doc.get("section", ""),
            "articulo": doc_art,
            "hierarchy": " > ".join(filter(None, [doc.get("h1"), doc.get("h2"), doc.get("h3")])),
            "content": doc_content,
            "char_count": len(doc_content),
            "approx_tokens": len(doc_content.split())
        })

    return results

@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    subfolder: str = Form("02_codigos")
):
    cartridge_corpus = settings.CARTRIDGES_PATH / settings.ACTIVE_CARTRIDGE / "corpus" / subfolder
    cartridge_corpus.mkdir(parents=True, exist_ok=True)

    dest_path = cartridge_corpus / file.filename
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": f"Archivo '{file.filename}' subido con éxito al cartucho '{settings.ACTIVE_CARTRIDGE}'",
        "path": str(dest_path)
    }

@app.post("/api/ingest")
async def trigger_ingestion():
    pipeline = IngestionPipeline(
        cartridge_name=settings.ACTIVE_CARTRIDGE,
        vector_store=vector_store,
        bm25_index=bm25_index
    )
    count = await pipeline.ingest_corpus()
    return {"message": "Re-indexación finalizada con éxito", "total_chunks": count}

# -------------------------------------------------------------
# ENDPOINTS DE MEMORIA 'CEREBRO OBSIDIANO' (VAULT)
# -------------------------------------------------------------
@app.get("/api/vault/notes")
def get_vault_notes(category: Optional[str] = None):
    return vault_manager.list_notes(category=category)

@app.get("/api/vault/notes/{category}/{note_id}")
def get_vault_note_detail(category: str, note_id: str):
    note = vault_manager.get_note(category, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada en la bóveda.")
    return note

@app.post("/api/vault/notes")
def save_vault_note_endpoint(req: VaultNoteCreateRequest):
    path = vault_manager.save_note(
        category=req.category,
        note_id=req.note_id,
        title=req.title,
        content=req.content,
        metadata=req.metadata,
        tags=req.tags,
        links=req.links
    )
    return {"status": "saved", "path": str(path)}

# -------------------------------------------------------------
# SERVIDORES DE ARCHIVOS ESTÁTICOS DE LA INTERFAZ WEB
# -------------------------------------------------------------
web_dir = settings.BASE_DIR / "web"
web_dir.mkdir(parents=True, exist_ok=True)

app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
