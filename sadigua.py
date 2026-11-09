#!/usr/bin/env python
"""
SADIGUA - CLI de Control y Gestión del Cerebro Soberano
"""

import sys
import asyncio
from pathlib import Path

from config.settings import settings
from core.rag.bm25_index import PureBM25Index
from core.rag.vector_store import LocalVectorStore
from core.rag.hybrid_retriever import HybridRetriever
from core.rag.reranker import PrecisionReranker
from core.rag.ingest import IngestionPipeline
from core.memory.vault_manager import ObsidianVaultManager
from core.agents.orchestrator import SadiguaOrchestrator
from core.engine.factory import get_llm_engine

async def cmd_ingest():
    print(f"[*] Iniciando ingesta documental para el cartucho '{settings.ACTIVE_CARTRIDGE}'...")
    pipeline = IngestionPipeline(cartridge_name=settings.ACTIVE_CARTRIDGE)
    total = await pipeline.ingest_corpus()
    print(f"[OK] Proceso finalizado. Total de fragmentos normativos en memoria: {total}")

async def cmd_chat():
    print("=" * 65)
    print("           SADIGUA - CEREBRO JURÍDICO & CONOCIMIENTO")
    print(f" Proveedor: [{settings.LLM_PROVIDER.upper()}]  |  Cartucho: [{settings.ACTIVE_CARTRIDGE}]")
    print(" Escribe tu consulta legal o caso. Escribe 'salir' para terminar.")
    print("=" * 65 + "\n")

    # Iniciar componentes
    vault = ObsidianVaultManager()
    bm25 = PureBM25Index()
    vector_store = LocalVectorStore()

    # Cargar documentos en memoria
    pipeline = IngestionPipeline(cartridge_name=settings.ACTIVE_CARTRIDGE, vector_store=vector_store, bm25_index=bm25)
    await pipeline.ingest_corpus()

    retriever = HybridRetriever(bm25_index=bm25, vector_store=vector_store)
    reranker = PrecisionReranker()
    orchestrator = SadiguaOrchestrator(
        cartridge_name=settings.ACTIVE_CARTRIDGE,
        llm_engine=get_llm_engine(),
        retriever=retriever,
        reranker=reranker,
        vault_manager=vault
    )

    while True:
        try:
            query = input("\n[Abogado/Usuario] > ").strip()
            if not query:
                continue
            if query.lower() in ["salir", "exit", "quit"]:
                print("\nCerrando sesión de Sadigua.")
                break

            print("\n[Sadigua analizando precedentes y fuentes normativas...]")
            res = await orchestrator.answer(query)

            print("\n" + "-" * 65)
            print("[RESPUESTA FUNDAMENTADA EN DERECHO]:")
            print(res["answer"])
            print("-" * 65)

            if res.get("sources"):
                print("\n[Fuentes Normativas Consultadas]:")
                for s in res["sources"]:
                    print(f" - {s.get('source')} | {s.get('articulo') or s.get('section')}")

            print(f"\n[Control Anti-Alucinación]: {res.get('grounding_status')}")

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"\n[!] Error en procesamiento: {e}")

def cmd_vault():
    vault = ObsidianVaultManager()
    notes = vault.list_notes()
    print("=" * 65)
    print(f" BÓVEDA OBSIDIAN ('Cerebro Obsidiano') - Total: {len(notes)} notas")
    print(f" Ruta en Windows: {settings.VAULT_PATH}")
    print("=" * 65)
    for n in notes:
        print(f" • [{n['category'].upper()}] {n['title']} (id: {n['id']})")
        print(f"   Última actualización: {n['updated']}")
        print(f"   Extracto: {n['snippet']}")
        print()

def cmd_sync(commit_msg="Update Sadigua core and knowledge base"):
    import subprocess
    print("=" * 65)
    print("SADIGUA - SINCRONIZADOR DUAL (GIT & GOOGLE DRIVE)")
    print("=" * 65)

    base_dir = str(settings.BASE_DIR)
    gdrive_dest = Path("G:/My Drive/AI_BOCHICA/Sadigua")

    # 1. Sincronización con Git Local
    print("\n[1/3] Sincronizando repositorio Git local...")
    try:
        subprocess.run(["git", "add", "."], cwd=base_dir, check=True)
        # Comprobar si hay cambios para commitear
        status_res = subprocess.run(["git", "status", "--porcelain"], cwd=base_dir, capture_output=True, text=True)
        if status_res.stdout.strip():
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=base_dir, check=True)
            print(f"[OK] Commit local creado: '{commit_msg}'")
        else:
            print("[*] Repositorio Git limpio, sin cambios pendientes.")
    except Exception as e:
        print(f"[!] Advertencia en Git local: {e}")

    # 2. Sincronización con GitHub (Remote)
    print("\n[2/3] Verificando sincronización con GitHub Remoto...")
    try:
        remotes_res = subprocess.run(["git", "remote"], cwd=base_dir, capture_output=True, text=True)
        if "origin" in remotes_res.stdout:
            push_res = subprocess.run(["git", "push", "origin", "main"], cwd=base_dir, capture_output=True, text=True)
            if push_res.returncode == 0:
                print("[OK] Sincronizado exitosamente con GitHub (branch 'main').")
            else:
                print(f"[!] Git push falló o requiere autenticación: {push_res.stderr.strip()}")
        else:
            print("[*] No hay remote 'origin' configurado aún.")
            print("    Para vincular tu repositorio de GitHub ejecuta:")
            print("    git remote add origin https://github.com/Zergiobg/<tu-repo>.git")
            print("    git push -u origin main")
    except Exception as e:
        print(f"[!] Error comunicando con GitHub: {e}")

    # 3. Sincronización con Google Drive
    print(f"\n[3/3] Sincronizando con Google Drive ({gdrive_dest})...")
    if Path("G:/My Drive").exists():
        gdrive_dest.mkdir(parents=True, exist_ok=True)
        # Usar robocopy para espejo rápido en Windows
        cmd_robo = [
            "robocopy", base_dir, str(gdrive_dest),
            "/E", "/XD", ".git", ".venv", "venv", "__pycache__", "data", ".ollama",
            "/XF", ".env", "*.gguf", "*.bin",
            "/R:1", "/W:1",
            "/NFL", "/NDL", "/NJH", "/NJS"
        ]
        res_robo = subprocess.run(cmd_robo, capture_output=True)
        # En robocopy, valores menores a 8 indican éxito (0: sin cambios, 1: archivos copiados, 2/3: extras/actualizados)
        if res_robo.returncode < 8:
            print(f"[OK] Proyecto Sadigua sincronizado al 100% en Google Drive.")
            print(f"     Ubicación: G:\\My Drive\\AI_BOCHICA\\Sadigua")
        else:
            print(f"[!] Código de salida robocopy: {res_robo.returncode}")
    else:
        print("[!] No se detectó la unidad G:\\My Drive de Google Drive for Desktop en este equipo.")

    print("\n" + "=" * 65)
    print("PROCESO DE SINCRONIZACIÓN FINALIZADO")
    print("=" * 65)

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "info":
        print(f"SADIGUA - Versión 1.0.0")
        print(f"Motor LLM: {settings.LLM_PROVIDER}")
        print(f"Cartucho Activo: {settings.ACTIVE_CARTRIDGE}")
        print(f"Ruta Bóveda: {settings.VAULT_PATH}")
        print("\nComandos disponibles:")
        print("  python sadigua.py web       -> Inicia el servidor Web y la interfaz gráfica (puerto 7837)")
        print("  python sadigua.py chat      -> Inicia sesión de consulta jurídica en terminal")
        print("  python sadigua.py ingest    -> Re-indexa el corpus del cartucho activo")
        print("  python sadigua.py vault     -> Lista los expedientes y notas del Cerebro Obsidiano")
        print("  python sadigua.py sync      -> Sincroniza automáticamente con Git y Google Drive")
        return

    cmd = sys.argv[1]
    if cmd == "web":
        import uvicorn
        print(f"[*] Iniciando SADIGUA Web en http://localhost:{settings.PORT}")
        uvicorn.run("gateway.api:app", host=settings.HOST, port=settings.PORT, reload=False)
    elif cmd == "sync":
        msg = sys.argv[2] if len(sys.argv) > 2 else "Update Sadigua core and knowledge base"
        cmd_sync(msg)
    elif cmd == "ingest":
        asyncio.run(cmd_ingest())
    elif cmd == "chat":
        asyncio.run(cmd_chat())
    elif cmd == "vault":
        cmd_vault()
    else:
        print(f"Comando desconocido: {cmd}")

if __name__ == "__main__":
    main()
