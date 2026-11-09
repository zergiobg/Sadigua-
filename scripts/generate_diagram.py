import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

def create_final_architecture_diagram():
    output_dir = Path(__file__).resolve().parent.parent / "docs"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "diagrama_arquitectura_final_sadigua.png"

    fig, ax = plt.subplots(figsize=(16, 11.2), dpi=220)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Fondo blanco general
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Título General Superior
    ax.text(50, 97.6, "ARQUITECTURA FINAL IMPLEMENTADA — SADIGUA: SLM SOBERANO + AGENTES DESACOPLADOS",
            fontsize=14.5, fontweight="bold", ha="center", va="center", color="#0F172A", family="sans-serif")

    # Borde Verde Dashed de Soberanía On-Premise
    green_border = patches.FancyBboxPatch((2.2, 2.5), 95.6, 92.5,
                                         boxstyle="round,pad=0.5,rounding_size=1.0",
                                         facecolor="none", edgecolor="#15803D", linestyle="--", linewidth=1.8)
    ax.add_patch(green_border)
    ax.text(50, 93.6, "ENTORNO SOBERANO LOCAL ON-PREMISE — AIR-GAP GATE (Ley 1581 / CONPES 4144)",
            fontsize=11, fontweight="bold", ha="center", va="center", color="#15803D", family="sans-serif")

    # Helper para dibujar cajas con espaciado vertical dinámico anti-solapamiento
    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color, title_color="#0F172A", sub_color="#334155", fontsize=9.2, sub_fontsize=7.6):
        box = patches.FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.3,rounding_size=0.6",
                                    facecolor=bg_color, edgecolor=border_color, linewidth=1.4)
        ax.add_patch(box)
        if subtitle:
            title_lines = title.count("\n") + 1
            if title_lines == 1:
                title_y = y + h * 0.73
                sub_y = y + h * 0.36
            else:
                title_y = y + h * 0.77
                sub_y = y + h * 0.32
            ax.text(x + w/2, title_y, title, fontsize=fontsize, fontweight="bold", ha="center", va="center", color=title_color, family="sans-serif")
            ax.text(x + w/2, sub_y, subtitle, fontsize=sub_fontsize, ha="center", va="center", color=sub_color, family="sans-serif")
        else:
            ax.text(x + w/2, y + h*0.5, title, fontsize=fontsize, fontweight="bold", ha="center", va="center", color=title_color, family="sans-serif")

    # Helper para flechas
    def draw_arrow(x1, y1, x2, y2, color="#475569", width=1.4, style="->"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=width, shrinkA=0, shrinkB=0))

    # -------------------------------------------------------------
    # CAPA 1: CANALES (Y: 81.0 a 89.5)
    # -------------------------------------------------------------
    c_w = 21.6
    c_h = 8.5
    c_y = 81.0

    # 1. Web SPA
    draw_box(4.5, c_y, c_w, c_h,
             "WEB / APP SPA (Puerto 7837)",
             "Ciudadano / Operador Legal\nAzul, Gris, Blanco (Cero Dark Mode)",
             "#EFF6FF", "#3B82F6", "#1D4ED8", "#1E3A8A")
    # 2. WhatsApp
    draw_box(28.0, c_y, c_w, c_h,
             "WHATSAPP BOT",
             "Webhook REST (POST /api/chat)\nIntegración Baileys / Evolution",
             "#EFF6FF", "#3B82F6", "#1D4ED8", "#1E3A8A")
    # 3. Voz
    draw_box(51.5, c_y, c_w, c_h,
             "VOZ LOCAL (Whisper / Piper)",
             "Agente Telefónico Soberano\nInferencia directa sin latencia",
             "#EFF6FF", "#3B82F6", "#1D4ED8", "#1E3A8A")
    # 4. Portales Internos
    draw_box(75.0, c_y, c_w, c_h,
             "PORTALES INTERNOS",
             "Consola Bóveda / Cartuchos / Chunks\nExpedientes y Auditoría RAG",
             "#EFF6FF", "#3B82F6", "#1D4ED8", "#1E3A8A")

    # -------------------------------------------------------------
    # CAPA 2: API GATEWAY & PII (Y: 68.0 a 75.5)
    # -------------------------------------------------------------
    gw_w = 70.0
    gw_h = 7.5
    gw_x = 15.0
    gw_y = 68.0
    draw_box(gw_x, gw_y, gw_w, gw_h,
             "API GATEWAY + BACKEND (FastAPI en gateway/api.py)",
             "Autenticación · PII Shield (gateway/anonymizer.py) · Trazabilidad · Compuerta Air-Gap",
             "#FFF7ED", "#EA580C", "#9A3412", "#C2410C", fontsize=10, sub_fontsize=8.2)

    # Flechas de canales a Gateway
    draw_arrow(15.3, c_y, 25.0, gw_y + gw_h)
    draw_arrow(38.8, c_y, 40.0, gw_y + gw_h)
    draw_arrow(62.3, c_y, 60.0, gw_y + gw_h)
    draw_arrow(85.8, c_y, 75.0, gw_y + gw_h)

    # -------------------------------------------------------------
    # CAPA 3: ORQUESTADOR & HUMAN IN THE LOOP (Y: 54.5 a 62.5)
    # -------------------------------------------------------------
    orq_w = 46.0
    orq_h = 8.0
    orq_x = 22.0
    orq_y = 54.5
    draw_box(orq_x, orq_y, orq_w, orq_h,
             "ORQUESTADOR DE AGENTES (SadiguaOrchestrator)",
             "Planes Verificables · Recuperación Híbrida · Rerank Neural · Validación de Citas",
             "#FAF5FF", "#9333EA", "#6B21A8", "#7E22CE", fontsize=9.8, sub_fontsize=8.0)

    # Flecha de Gateway a Orquestador
    draw_arrow(50.0, gw_y, 50.0, orq_y + orq_h)

    # Human in the Loop (a la derecha)
    hitl_w = 20.5
    hitl_h = 8.0
    hitl_x = 74.5
    hitl_y = 54.5
    draw_box(hitl_x, hitl_y, hitl_w, hitl_h,
             "HUMAN-IN-THE-LOOP",
             "GroundingValidator\nEscalamiento ante falta de normas",
             "#FEF2F2", "#DC2626", "#991B1B", "#B91C1C", fontsize=9.2, sub_fontsize=7.8)

    # Flecha bidireccional Orquestador <-> HITL
    draw_arrow(orq_x + orq_w, orq_y + orq_h*0.65, hitl_x, hitl_y + hitl_h*0.65, color="#DC2626", width=1.4, style="->")
    draw_arrow(hitl_x, hitl_y + hitl_h*0.35, orq_x + orq_w, orq_y + orq_h*0.35, color="#DC2626", width=1.4, style="->")

    # -------------------------------------------------------------
    # CAPA 4: INFERENCIA, MEMORIA OBSIDIANA & MCP (Y: 37.5 a 49.0)
    # -------------------------------------------------------------
    # Izquierda: Cerebro Obsidiano
    obs_w = 21.5
    obs_h = 11.5
    obs_x = 4.5
    obs_y = 37.5
    draw_box(obs_x, obs_y, obs_w, obs_h,
             "MEMORIA PERSISTENTE\n\"Cerebro Obsidiano\"",
             "Bóveda Markdown en vault/\nFichas de clientes y expedientes\nYAML frontmatter + Enlaces [[wiki]]\nAuditables 100% en App Obsidian",
             "#F5F3FF", "#7C3AED", "#5B21B6", "#4C1D95", fontsize=9.0, sub_fontsize=7.4)

    # Centro: Motor de Inferencia Local
    llm_w = 43.0
    llm_h = 11.5
    llm_x = 28.5
    llm_y = 37.5
    draw_box(llm_x, llm_y, llm_w, llm_h,
             "MOTOR DE INFERENCIA SOBERANO (Ollama Local)",
             "SLM Qwen 2.5 7B / 14B Instruct (GGUF Cuantizado)\nEjecución en CPU Intel Core Ultra (8-12 hilos AVX2)\nCero Salida Externa (Air-Gap Gate) · Costo $0.00 / token\nLatencia TTFT: 0.8s - 1.4s · 8 a 15 tokens/seg",
             "#F0FDF4", "#16A34A", "#14532D", "#166534", fontsize=9.8, sub_fontsize=7.8)

    # Derecha: MCP Server / Cartuchos (CORREGIDO: mcp_x en vez de mcp_w!)
    mcp_w = 21.5
    mcp_h = 11.5
    mcp_x = 74.0
    mcp_y = 37.5
    draw_box(mcp_x, mcp_y, mcp_w, mcp_h,
             "MCP SERVER / CARTUCHOS\n(Herramientas Desacopladas)",
             "cartridges/legal_co · telco_crm\nHerramientas y Prompts aislados\nPermisos y schemas por tool\nIntercambiables en caliente",
             "#F5F3FF", "#7C3AED", "#5B21B6", "#4C1D95", fontsize=9.0, sub_fontsize=7.4)

    # Flechas Orquestador hacia Capa 4
    draw_arrow(28.0, orq_y, obs_x + obs_w*0.5, obs_y + obs_h)
    draw_arrow(50.0, orq_y, 50.0, llm_y + llm_h)
    draw_arrow(72.0, orq_y, mcp_x + mcp_w*0.5, mcp_y + mcp_h)

    # Flechas horizontales Cerebro <-> LLM y LLM <-> MCP
    draw_arrow(obs_x + obs_w, obs_y + obs_h*0.5, llm_x, llm_y + llm_h*0.5, color="#7C3AED", width=1.4)
    draw_arrow(llm_x + llm_w, llm_y + llm_h*0.5, mcp_x, mcp_y + mcp_h*0.5, color="#7C3AED", width=1.4)

    # -------------------------------------------------------------
    # CAPA 5: PIPELINE RAG & BASES VECTORIALES (Y: 22.0 a 32.5)
    # -------------------------------------------------------------
    rag_h = 10.5
    rag_y = 22.0

    # 1. Pipeline RAG
    rag_w = 28.0
    rag_x = 4.5
    draw_box(rag_x, rag_y, rag_w, rag_h,
             "PIPELINE RAG HÍBRIDO",
             "LegalHierarchicalChunker (Libro/Tít/Art)\nBúsqueda Léxica BM25 + Embeddings BGE\nFusión RRF (k=60) + PrecisionReranker",
             "#ECFEFF", "#0891B2", "#155E75", "#0E7490", fontsize=9.2, sub_fontsize=7.6)

    # 2. Bases Vectoriales
    vec_w = 31.0
    vec_x = 35.0
    draw_box(vec_x, rag_y, vec_w, rag_h,
             "BASES VECTORIALES HÍBRIDAS",
             "LocalVectorStore embebido (JSON en RAM)\nChromaDB en Docker (vectorstore persistente)\nSimilitud Coseno directa sin latencia nube",
             "#ECFEFF", "#0891B2", "#155E75", "#0E7490", fontsize=9.2, sub_fontsize=7.6)

    # 3. Documentos Oficiales
    doc_w = 27.5
    doc_x = 68.0
    draw_box(doc_x, rag_y, doc_w, rag_h,
             "DOCUMENTOS OFICIALES",
             "Normas · CGP · Ley 1581 · Resoluciones CRC\nExtracción PDF nativa vía pypdf en ingest.py\nCarga incremental por UI web o CLI",
             "#ECFEFF", "#0891B2", "#155E75", "#0E7490", fontsize=9.2, sub_fontsize=7.6)

    # Flechas horizontales entre RAG, Vectores y Documentos
    draw_arrow(rag_x + rag_w, rag_y + rag_h*0.5, vec_x, rag_y + rag_h*0.5, color="#0891B2", width=1.4)
    draw_arrow(doc_x, rag_y + rag_h*0.5, vec_x + vec_w, rag_y + rag_h*0.5, color="#0891B2", width=1.4)

    # Flecha vertical desde Bases Vectoriales hacia Motor de Inferencia
    draw_arrow(50.0, rag_y + rag_h, 50.0, llm_y, color="#0891B2", width=1.4)

    # -------------------------------------------------------------
    # CAPA 6: LLMOPS, GOBERNANZA & INFRAESTRUCTURA (Y: 5.5 a 16.0)
    # -------------------------------------------------------------
    b_h = 10.5
    b_y = 5.5

    # 1. LLMOps
    b1_w = 28.0
    b1_x = 4.5
    draw_box(b1_x, b_y, b1_w, b_h,
             "LLMOps: EVALS & TRACING",
             "Suite Automatizada tests/run_tests.py (10/10)\nGroundingValidator: Verificación Citas Fácticas\nTelemetría de Hardware y Costo $0.00 / token",
             "#FFFBEB", "#D97706", "#92400E", "#78350F", fontsize=9.2, sub_fontsize=7.6)

    # 2. Gobernanza
    b2_w = 31.0
    b2_x = 35.0
    draw_box(b2_x, b_y, b2_w, b_h,
             "GOBERNANZA & COMPLIANCE",
             "Model Cards (manifest.yaml por cartucho)\nAuditoría de Fuentes y Explicabilidad total\nTemperatura 0.1 · Citación obligatoria",
             "#FFFBEB", "#D97706", "#92400E", "#78350F", fontsize=9.2, sub_fontsize=7.6)

    # 3. Infraestructura
    b3_w = 27.5
    b3_x = 68.0
    draw_box(b3_x, b_y, b3_w, b_h,
             "INFRA & DESPLIEGUE PORTABLE",
             "HardwareProfiler: Detección Cores / RAM\nKit USB Portable (PREPARAR_USB.bat)\nComando Antigravity 'deploy Sadigua' · Sync Dual",
             "#FFFBEB", "#D97706", "#92400E", "#78350F", fontsize=9.2, sub_fontsize=7.6)

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=220, bbox_inches="tight", facecolor="#FFFFFF")
    plt.close()
    print(f"[OK] Diagrama de arquitectura final corregido y generado en: {output_path}")
    return output_path

if __name__ == "__main__":
    create_final_architecture_diagram()
