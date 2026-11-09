import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from config.settings import settings
from core.engine.factory import get_llm_engine
from core.engine.gemini_engine import GeminiEngine
from core.agents.grounding_check import GroundingValidator
from core.rag.bm25_index import PureBM25Index
from core.rag.vector_store import LocalVectorStore
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import PrecisionReranker
from core.rag.ingest import IngestionPipeline
from core.memory.vault_manager import ObsidianVaultManager
from core.agents.orchestrator import SadiguaOrchestrator
from core.cartridges.manager import CartridgeManager
from core.rag.mutation_engine import LexMutationEngine
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

def _persist_env_var(key: str, value: str):
    env_path = settings.BASE_DIR / ".env"
    lines = []
    found = False
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line_s = line.strip()
            if line_s.startswith(f"{key}=") or line_s.startswith(f"{key} ="):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(line)
    if not found:
        lines.append(f"{key}={value}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Modelos Pydantic para peticiones
class ChatRequest(BaseModel):
    message: str = Field(..., description="Consulta del usuario")
    anonymize: bool = Field(default=True, description="Enmascarar datos personales (Ley 1581)")
    skip_cache: bool = Field(default=False, description="Omitir caché de precedentes y forzar búsqueda RAG fresca")

class CheckIntentRequest(BaseModel):
    message: str

class PrecedentAnswerRequest(BaseModel):
    note_id: str
    query: str

class RecordMutationRequest(BaseModel):
    source_doc: str
    target_norm: str
    mutation_type: str = "OVERRULING"
    regla_anterior: str
    regla_nueva: str
    autoridad: str = "Corte Constitucional / Consejo de Estado"
    fecha_mutacion: Optional[str] = None
    efectos: str = "Hacia el futuro (Ex nunc)"
    curator_notes: str = ""

class SwitchCartridgeRequest(BaseModel):
    cartridge_id: str = Field(..., description="ID del cartucho a activar")

class ConfigUpdateRequest(BaseModel):
    llm_provider: Optional[str] = Field(default=None, description="'gemini' o 'local'")
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
    key_val = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    masked_key = f"{key_val[:6]}...{key_val[-4:]}" if len(key_val) > 10 else ("Configurada" if key_val else "")
    return {
        "status": "online",
        "provider": settings.LLM_PROVIDER,
        "cloud_egress_enabled": settings.CLOUD_EGRESS_ENABLED,
        "active_cartridge": settings.ACTIVE_CARTRIDGE,
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_configured": bool(key_val),
        "gemini_masked_key": masked_key,
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
    if req.llm_provider is not None:
        if req.llm_provider not in ["gemini", "local"]:
            raise HTTPException(status_code=400, detail="Proveedor inválido. Use 'gemini' o 'local'.")
        settings.LLM_PROVIDER = req.llm_provider

    if req.cloud_egress_enabled is not None:
        settings.CLOUD_EGRESS_ENABLED = req.cloud_egress_enabled

    if req.gemini_api_key is not None:
        cleaned_key = req.gemini_api_key.strip()
        settings.GEMINI_API_KEY = cleaned_key
        os.environ["GEMINI_API_KEY"] = cleaned_key
        if cleaned_key:
            _persist_env_var("GEMINI_API_KEY", cleaned_key)

    if req.gemini_model:
        settings.GEMINI_MODEL = req.gemini_model.strip()
        _persist_env_var("GEMINI_MODEL", settings.GEMINI_MODEL)

    if req.local_base_url:
        settings.LOCAL_BASE_URL = req.local_base_url.strip()
    if req.local_model:
        settings.LOCAL_MODEL = req.local_model.strip()

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

@app.post("/api/chat/check-intent")
def check_intent_endpoint(req: CheckIntentRequest):
    """
    Antesala interactiva: evalúa si la consulta coincide conceptualmente
    con algún precedente en la Bóveda de Obsidian. Responde en 2 milisegundos.
    """
    user_query = req.message.strip()
    if not user_query:
        return {"found": False}
    candidate = orchestrator.semantic_cache.find_candidate_precedent(user_query, threshold=0.60)
    if candidate:
        return candidate
    return {"found": False}

@app.post("/api/chat/precedent-answer")
def precedent_answer_endpoint(req: PrecedentAnswerRequest):
    """
    Retorna instantáneamente el dictamen y ruta procesal del precedente confirmado por el usuario.
    """
    note = vault_manager.get_note("consultas", req.note_id)
    if not note:
        # Fallback al contenido indexado en memoria
        for e in orchestrator.semantic_cache.entries:
            if e.get("note_id") == req.note_id and e.get("answer"):
                note = {
                    "content": e["answer"],
                    "metadata": {
                        "query": e.get("query"),
                        "grounding_status": e.get("grounding_status"),
                        "created_at": e.get("created_at"),
                        "sources": e.get("sources", [])
                    }
                }
                break
    if not note:
        raise HTTPException(status_code=404, detail="Precedente no encontrado en la bóveda.")

    content = note.get("content", "")
    metadata = note.get("metadata", {})

    # Registrar en memoria de conversación
    orchestrator.memory.add_user_message(req.query)
    orchestrator.memory.add_assistant_message(content, citations=[])

    return {
        "status": "success",
        "answer": content,
        "note_id": req.note_id,
        "matched_query": metadata.get("query", req.query),
        "grounding_status": metadata.get("grounding_status", "✓ Precedente Verificado en Bóveda"),
        "created_at": metadata.get("created_at", ""),
        "sources": metadata.get("sources", [])
    }

@app.post("/api/chat/progressive")
async def chat_progressive_endpoint(request: ChatRequest):
    """
    Endpoint SSE (Server-Sent Events) para Generación Progresiva en Ondas
    y Telemetría Activa (cronómetro, fases, documentos RAG en tiempo real).
    """
    user_query = request.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    mapping = {}
    if request.anonymize:
        user_query, mapping = PIIAnonymizer.mask(user_query)

    async def sse_event_stream():
        try:
            async for event in orchestrator.answer_progressive_stream(user_query, skip_cache=request.skip_cache):
                # Si hubo enmascaramiento de PII, restaurar en los textos que se envíen
                if request.anonymize and mapping:
                    if event.get("type") == "token" and "text" in event:
                        event["text"] = PIIAnonymizer.unmask(event["text"], mapping)
                    elif event.get("type") == "precedent_hit" and "answer" in event:
                        event["answer"] = PIIAnonymizer.unmask(event["answer"], mapping)

                data_str = json.dumps(event, ensure_ascii=False)
                yield f"data: {data_str}\n\n"
        except Exception as e:
            err_data = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            yield f"data: {err_data}\n\n"

    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/chat/gemini-stream")
async def chat_gemini_stream_endpoint(request: ChatRequest):
    """
    Endpoint SSE pedagógico para comparación paralela en tiempo real
    entre el Modelo Local Soberano y Google Gemini Cloud.
    """
    user_query = request.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        async def err_stream():
            msg = "Clave de API de Gemini (GEMINI_API_KEY) no configurada. Ingrésala en la sección 'Configuración MLOps' para habilitar la columna de comparación."
            yield f"data: {json.dumps({'type': 'error', 'message': msg}, ensure_ascii=False)}\n\n"
        return StreamingResponse(
            err_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    mapping = {}
    if request.anonymize:
        user_query, mapping = PIIAnonymizer.mask(user_query)

    async def sse_gemini_stream():
        import time
        start_time = time.time()
        ttft = None
        token_count = 0
        full_text = ""
        try:
            yield f"data: {json.dumps({'type': 'phase', 'phase': 'gemini_retrieval', 'message': 'Recuperando contexto normativo idéntico para competencia justa...'}, ensure_ascii=False)}\n\n"

            # Recuperar los mismos documentos normativos para que la evaluación sea 100% ecuánime
            candidates = await retriever.retrieve(user_query, top_k=6)
            retrieved_docs = reranker.rerank(user_query, candidates, top_n=3)

            context_blocks = []
            for idx, doc in enumerate(retrieved_docs, start=1):
                source_label = doc.get("source", "Norma")
                section_label = doc.get("section", "")
                art_label = doc.get("articulo", "")
                header = f"[Fuente {idx}: {source_label} | {art_label or section_label}]"
                context_blocks.append(f"{header}\n{doc.get('content', '')}")
            context_str = "\n\n---\n\n".join(context_blocks)

            yield f"data: {json.dumps({'type': 'phase', 'phase': 'gemini_start', 'message': 'Conectando con Google Gemini en la nube...'}, ensure_ascii=False)}\n\n"

            gemini_prompt = (
                f"CONSULTA DEL USUARIO / CASO JURÍDICO:\n{user_query}\n\n"
                f"FUENTES NORMATIVAS Y JURISPRUDENCIALES CURADAS DISPONIBLES:\n"
                f"{context_str if context_str else '[NO SE DISPONE DE FUENTES ESPECÍFICAS PARA ESTA CONSULTA]'}\n\n"
                "ESTRUCTURA OBLIGATORIA DEL DICTAMEN JURÍDICO:\n"
                "1. ### Veredicto Jurídico Directo\n"
                "2. ### Fundamento Normativo Aplicable (Cita solo las normas estrictamente aplicables)\n"
                "3. ### Análisis y Subsunción Jurídica\n"
                "4. ### Ruta Procesal Paso a Paso (Reclamación previa, Denuncia SIC)\n"
                "5. ### Acciones Judiciales (Tutela, Demanda Civil)\n"
                "6. ### Conclusión y Recomendaciones Prácticas Finales\n\n"
                "REGLAS:\n"
                "- Rigor y prudencia jurídica en derecho colombiano.\n"
                "- Cierra todas las ideas con punto final."
            )

            engine = GeminiEngine(api_key=api_key, model=settings.GEMINI_MODEL)

            async for token in engine.stream(
                prompt=gemini_prompt,
                system_prompt=orchestrator.system_prompt,
                temperature=0.1,
                max_tokens=2500
            ):
                if ttft is None:
                    ttft = round(time.time() - start_time, 2)
                    yield f"data: {json.dumps({'type': 'ttft', 'ttft': ttft}, ensure_ascii=False)}\n\n"

                token_count += 1
                full_text += token
                out_token = PIIAnonymizer.unmask(token, mapping) if request.anonymize and mapping else token
                yield f"data: {json.dumps({'type': 'token', 'text': out_token}, ensure_ascii=False)}\n\n"

            total_time = round(time.time() - start_time, 2)
            tok_s = round(token_count / total_time, 1) if total_time > 0 else 0

            # Grounding check
            is_grounded, grounding_msg, citations = GroundingValidator.validate(full_text, retrieved_docs)

            yield f"data: {json.dumps({
                'type': 'done',
                'total_time': total_time,
                'ttft': ttft or total_time,
                'tokens': token_count,
                'tokens_per_sec': tok_s,
                'grounded': is_grounded,
                'grounding_status': grounding_msg,
                'citations': citations
            }, ensure_ascii=False)}\n\n"

        except Exception as e:
            err_data = json.dumps({"type": "error", "message": f"Error en Google Gemini Cloud: {str(e)}"}, ensure_ascii=False)
            yield f"data: {err_data}\n\n"

    return StreamingResponse(
        sse_gemini_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/vault/consultas")
def list_vault_consultas():
    """Retorna el catálogo de precedentes indexados en vault/consultas/"""
    return {
        "total_consultas": len(orchestrator.semantic_cache.entries),
        "consultas": orchestrator.semantic_cache.entries
    }

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
    subfolder: str = Form("02_codigos"),
    curator_instruction: Optional[str] = Form(None)
):
    cartridge_corpus = settings.CARTRIDGES_PATH / settings.ACTIVE_CARTRIDGE / "corpus" / subfolder
    cartridge_corpus.mkdir(parents=True, exist_ok=True)

    dest_path = cartridge_corpus / file.filename
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    mutation_info = None
    if curator_instruction and curator_instruction.strip():
        pipeline = IngestionPipeline(
            cartridge_name=settings.ACTIVE_CARTRIDGE,
            vector_store=vector_store,
            bm25_index=bm25_index
        )
        await pipeline.ingest_corpus(curator_instruction=curator_instruction.strip(), current_file=file.filename)
        mutations = LexMutationEngine().list_mutations(limit=1)
        if mutations:
            mutation_info = mutations[0]

    return {
        "message": f"Archivo '{file.filename}' subido con éxito al cartucho '{settings.ACTIVE_CARTRIDGE}'",
        "path": str(dest_path),
        "mutation_registered": mutation_info is not None,
        "mutation": mutation_info
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
# ENDPOINTS DE TRAZABILIDAD Y MUTACIÓN DE PRECEDENTES (SQLITE)
# -------------------------------------------------------------
@app.get("/api/jurisprudencia/mutations")
def get_jurisprudencia_mutations(limit: int = 50, q: Optional[str] = None):
    """Retorna las mutaciones normativas registradas en SQLite y sincronizadas con Obsidian."""
    engine = LexMutationEngine()
    if q:
        return engine.find_mutations_for_norm(q)
    return engine.list_mutations(limit=limit)

@app.post("/api/jurisprudencia/record-mutation")
def record_jurisprudencia_mutation(req: RecordMutationRequest):
    """Permite registrar manualmente una mutación de precedente o derogatoria formal."""
    engine = LexMutationEngine()
    mut_id = engine.record_mutation(
        source_doc=req.source_doc,
        target_norm=req.target_norm,
        mutation_type=req.mutation_type,
        regla_anterior=req.regla_anterior,
        regla_nueva=req.regla_nueva,
        autoridad=req.autoridad,
        fecha_mutacion=req.fecha_mutacion,
        efectos=req.efectos,
        curator_notes=req.curator_notes
    )
    return {"status": "success", "mutation_id": mut_id}

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
