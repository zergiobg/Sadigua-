from gateway.anonymizer import PIIAnonymizer
from core.memory.vault_manager import ObsidianVaultManager
from core.rag.chunker import LegalHierarchicalChunker
from core.rag.bm25_index import PureBM25Index
from core.agents.grounding_check import GroundingValidator
from core.engine.factory import get_llm_engine
from core.engine.gemini_engine import GeminiEngine
from core.engine.local_engine import LocalEngine
import tempfile
from pathlib import Path

def test_pii_anonymizer():
    raw_text = "El cliente Carlos Pérez con cédula 10203040 y correo carlitos@abogados.com llamó al +57 3101234567."
    masked, mapping = PIIAnonymizer.mask(raw_text)
    
    assert "carlitos@abogados.com" not in masked
    assert "10203040" not in masked
    assert "[EMAIL_" in masked
    assert "[ID_" in masked

    unmasked = PIIAnonymizer.unmask(masked, mapping)
    assert "carlitos@abogados.com" in unmasked
    assert "10203040" in unmasked

def test_obsidian_vault_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = ObsidianVaultManager(vault_path=Path(tmpdir))
        note_path = vault.save_note(
            category="expedientes",
            note_id="exp_001_tutela",
            title="Caso Tutela Derecho a la Salud",
            content="El accionante solicita entrega de medicamentos de alto costo.",
            metadata={"radicado": "2026-00123", "juzgado": "Segundo Civil del Circuito"},
            tags=["tutela", "salud", "urgente"],
            links=["cliente_perez", "sentencia_t760"]
        )
        assert note_path.exists()
        
        note = vault.get_note("expedientes", "exp_001_tutela")
        assert note is not None
        assert note["metadata"]["radicado"] == "2026-00123"
        assert "medicamentos de alto costo" in note["content"]

        notes_list = vault.list_notes("expedientes")
        assert len(notes_list) == 1
        assert notes_list[0]["id"] == "exp_001_tutela"

def test_legal_hierarchical_chunker():
    text = (
        "# CÓDIGO GENERAL DEL PROCESO\n"
        "## LIBRO SEGUNDO\n"
        "### SECCIÓN TERCERA\n"
        "#### ARTÍCULO 206. JURAMENTO ESTIMATORIO\n"
        "Quien pretenda el reconocimiento de una indemnización deberá estimarlo bajo juramento."
    )
    chunker = LegalHierarchicalChunker()
    chunks = chunker.chunk_markdown(text, source_path="cgp.md")
    assert len(chunks) == 1
    assert "ARTÍCULO 206" in chunks[0]["articulo"]
    assert "JURAMENTO ESTIMATORIO" in chunks[0]["section"]
    assert "LIBRO SEGUNDO" in chunks[0]["h2"]

    # Prueba con texto crudo extraído de PDF sin marcas de markdown
    raw_pdf_text = (
        "CONSTITUCIÓN POLÍTICA DE COLOMBIA\n"
        "TÍTULO II: DE LOS DERECHOS\n"
        "CAPÍTULO 1: DE LOS DERECHOS FUNDAMENTALES\n"
        "ARTÍCULO 11. El derecho a la vida es inviolable. No habrá pena de muerte.\n"
        "ARTÍCULO 12. Nadie será sometido a desaparición forzada...\n"
        "Artículo 15. Todas las personas tienen derecho a su intimidad...\n"
    )
    pdf_chunks = chunker.chunk_markdown(raw_pdf_text, source_path="constitucion.pdf")
    # 1 preámbulo/título + 3 artículos detectados
    assert len(pdf_chunks) == 4
    articles = [c for c in pdf_chunks if c["articulo"]]
    assert len(articles) == 3
    assert "ARTÍCULO 11" in articles[0]["articulo"]
    assert "ARTÍCULO 12" in articles[1]["articulo"]
    assert "Artículo 15" in articles[2]["articulo"]

def test_pure_bm25_exact_match():
    docs = [
        {"id": "doc_1", "content": "ARTÍCULO 206. Juramento estimatorio para reclamar indemnizaciones."},
        {"id": "doc_2", "content": "ARTÍCULO 167. Carga de la prueba en procesos civiles ordinarios."},
        {"id": "doc_3", "content": "ARTÍCULO 86. Acción de tutela ante jueces de la República."}
    ]
    bm25 = PureBM25Index()
    bm25.index(docs)

    results = bm25.search("juramento estimatorio artículo 206", top_k=1)
    assert len(results) == 1
    assert results[0][0]["id"] == "doc_1"

def test_grounding_validator():
    context = [{"content": "De conformidad con el Artículo 206 del CGP, el juramento estimatorio es obligatorio."}]
    
    # Respuesta respaldada
    valid_resp = "Según el Artículo 206, el juramento estimatorio debe presentarse con la demanda."
    is_valid, _, citations = GroundingValidator.validate(valid_resp, context)
    assert is_valid is True
    assert any("206" in c for c in citations)

    # Respuesta con alucinación de ley inexistente
    hallucinated_resp = "De acuerdo con el Artículo 9999 del Código de Comercio inventado, prescribe a los 100 años."
    is_valid_h, msg, _ = GroundingValidator.validate(hallucinated_resp, context)
    assert is_valid_h is False
    assert "Alucinación detectada" in msg

def test_engine_factory():
    from config.settings import settings

    # 1. Motor Local por defecto siempre disponible
    local_eng = get_llm_engine("local")
    assert isinstance(local_eng, LocalEngine)

    # 2. Con compuerta cerrada, Gemini debe lanzar PermissionError
    settings.CLOUD_EGRESS_ENABLED = False
    try:
        get_llm_engine("gemini")
        assert False, "Debería haber lanzado PermissionError"
    except PermissionError as e:
        assert "COMPUERTA DE SOBERANÍA" in str(e)

    # 3. Con compuerta abierta explícitamente, Gemini se permite
    settings.CLOUD_EGRESS_ENABLED = True
    gemini_eng = get_llm_engine("gemini")
    assert isinstance(gemini_eng, GeminiEngine)

    # Restaurar compuerta cerrada
    settings.CLOUD_EGRESS_ENABLED = False
