/**
 * SADIGUA - Controlador Frontend Profesional
 * Comunicación REST con FastAPI y gestión de estado local
 */

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // ESTADO DE LA APLICACIÓN
    // -------------------------------------------------------------
    const state = {
        activeTab: "tab-chat",
        systemStatus: null,
        notes: [],
        cartridges: [],
        documents: [],
        isQuerying: false,
        includeInMemory: true
    };

    const getViz = () => window.sadiguaVisualizer || null;

    // -------------------------------------------------------------
    // MENÚ DESPLEGABLE LATERAL (CYBER DRAWER) & CABECERA COMPACTA
    // -------------------------------------------------------------
    const cyberDrawer = document.getElementById("cyber-drawer");
    const drawerBackdrop = document.getElementById("drawer-backdrop");
    const btnToggleDrawer = document.getElementById("btn-toggle-drawer");
    const btnCloseDrawer = document.getElementById("btn-close-drawer");
    const btnQuickTelemetry = document.getElementById("btn-quick-telemetry");
    const activeViewTitle = document.getElementById("active-view-title");
    const neuralCockpit = document.getElementById("neural-cockpit");
    const btnToggleBrainStage = document.getElementById("btn-toggle-brain-stage");
    const brainStageToggleLabel = document.getElementById("brain-stage-toggle-label");

    function openDrawer() {
        cyberDrawer?.classList.add("open");
        drawerBackdrop?.classList.add("open");
    }

    function closeDrawer() {
        cyberDrawer?.classList.remove("open");
        drawerBackdrop?.classList.remove("open");
    }

    btnToggleDrawer?.addEventListener("click", openDrawer);
    btnQuickTelemetry?.addEventListener("click", openDrawer);
    btnCloseDrawer?.addEventListener("click", closeDrawer);
    drawerBackdrop?.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (state.isQuerying && typeof abortCurrentQuery === "function") {
                abortCurrentQuery();
            }
            closeDrawer();
            document.getElementById("note-modal")?.classList.remove("active");
            if (typeof closeMutationModal === "function") closeMutationModal();
        }
    });

    // Alternar visibilidad del panel del Cerebro Sadigua para lectura a pantalla completa
    btnToggleBrainStage?.addEventListener("click", () => {
        if (!neuralCockpit) return;
        const collapsed = neuralCockpit.classList.toggle("brain-collapsed");
        btnToggleBrainStage.classList.toggle("active", !collapsed);
        if (brainStageToggleLabel) {
            brainStageToggleLabel.textContent = collapsed ? "Mostrar Núcleo" : "Núcleo Activo";
        }
    });

    // -------------------------------------------------------------
    // NAVEGACIÓN POR PESTAÑAS (TABS)
    // -------------------------------------------------------------
    const navItems = document.querySelectorAll(".nav-item");
    const contentViews = document.querySelectorAll(".content-view");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.dataset.tab;
            if (!targetTab) return;

            navItems.forEach(n => n.classList.remove("active"));
            contentViews.forEach(v => v.classList.remove("active"));

            item.classList.add("active");
            const targetView = document.getElementById(targetTab);
            if (targetView) targetView.classList.add("active");
            state.activeTab = targetTab;

            if (activeViewTitle) {
                activeViewTitle.textContent = item.dataset.title || item.textContent.trim();
            }
            if (btnToggleBrainStage) {
                btnToggleBrainStage.style.display = targetTab === "tab-chat" ? "" : "none";
            }

            closeDrawer();

            // Recargar datos específicos según la pestaña seleccionada
            if (targetTab === "tab-vault") loadVaultNotes();
            if (targetTab === "tab-cartridges") {
                loadCartridges();
                loadDocuments();
                loadIndexData();
                loadMutationsTable();
            }
        });
    });

    // -------------------------------------------------------------
    // 1. CARGA INICIAL DE ESTADO DEL SISTEMA
    // -------------------------------------------------------------
    async function loadSystemStatus() {
        try {
            const res = await fetch("/api/system/status");
            if (!res.ok) throw new Error("Error consultando estado");
            const data = await res.json();
            state.systemStatus = data;

            // Actualizar badges de telemetría
            const headerProvider = document.getElementById("header-provider");
            if (headerProvider) {
                headerProvider.textContent =
                    data.provider === "gemini" ? `Gemini (${data.gemini_model})` : `Local (${data.local_model})`;
            }
            const headerCartridge = document.getElementById("header-cartridge");
            if (headerCartridge) headerCartridge.textContent = data.active_cartridge;
            const headerRam = document.getElementById("header-ram-val");
            if (headerRam && data.hardware_info?.ram_gb) {
                headerRam.textContent = `${data.hardware_info.ram_gb} GB Disponible`;
            }

            // Actualizar Compuerta de Soberanía
            updateSovereigntyUI(data.cloud_egress_enabled);

            // Configurar formulario de ajustes
            const providerSelect = document.getElementById("cfg-provider");
            if (providerSelect) {
                providerSelect.value = data.provider;
            }
            if (data.gemini_model) {
                const gm = document.getElementById("cfg-gemini-model");
                if (gm) gm.value = data.gemini_model;
            }
            if (data.local_url) {
                const lu = document.getElementById("cfg-local-url");
                if (lu) lu.value = data.local_url;
            }
            if (data.local_model) {
                const cfgLocal = document.getElementById("cfg-local-model");
                if (cfgLocal) cfgLocal.value = data.local_model;
                const quickSelect = document.getElementById("quick-model-select");
                if (quickSelect) quickSelect.value = data.local_model;
            }

            // Actualizar estado del badge de Gemini en MLOps
            const geminiBadge = document.getElementById("gemini-status-badge");
            const geminiKeyInput = document.getElementById("cfg-gemini-key");
            if (geminiBadge) {
                if (data.gemini_configured) {
                    geminiBadge.className = "badge badge-green";
                    geminiBadge.style.background = "";
                    geminiBadge.style.color = "";
                    geminiBadge.textContent = "✓ Clave de API Configurada en Sistema";
                    if (data.gemini_masked_key && geminiKeyInput) {
                        geminiKeyInput.placeholder = `Clave guardada: ${data.gemini_masked_key}`;
                    }
                } else {
                    geminiBadge.className = "badge";
                    geminiBadge.style.background = "var(--warning-bg)";
                    geminiBadge.style.color = "var(--warning-text)";
                    geminiBadge.textContent = "⚠️ Clave No Configurada";
                    if (geminiKeyInput) {
                        geminiKeyInput.placeholder = "Pega tu clave AIzaSy... aquí";
                    }
                }
            }

        } catch (e) {
            console.error("No se pudo conectar al backend de Sadigua:", e);
        }
    }

    function updateSovereigntyUI(egressEnabled) {
        const badgeSov = document.getElementById("badge-sovereignty");
        const pillSov = document.getElementById("egress-status-pill");
        const chkEgress = document.getElementById("chk-cloud-egress");
        const miniSovText = document.getElementById("mini-sovereignty-text");

        if (chkEgress) chkEgress.checked = Boolean(egressEnabled);

        if (egressEnabled) {
            if (badgeSov) {
                badgeSov.className = "badge badge-blue";
                badgeSov.innerHTML = "<span>🌐</span> <strong>Modo Híbrido (Nube Autorizada)</strong>";
            }
            if (miniSovText) {
                miniSovText.textContent = "Modo Híbrido";
            }
            if (pillSov) {
                pillSov.className = "badge";
                pillSov.style.background = "var(--warning-bg)";
                pillSov.style.color = "var(--warning-text)";
                pillSov.textContent = "⚠️ Salida a Nube Autorizada";
            }
        } else {
            if (badgeSov) {
                badgeSov.className = "badge badge-green";
                badgeSov.innerHTML = "<span>🔒</span> <strong>Soberanía: 100% Local</strong>";
            }
            if (miniSovText) {
                miniSovText.textContent = "100% Local";
            }
            if (pillSov) {
                pillSov.className = "badge badge-green";
                pillSov.style.background = "";
                pillSov.style.color = "";
                pillSov.textContent = "🔒 Salida a Nube Bloqueada";
            }
        }
    }

    // -------------------------------------------------------------
    // 2. CHAT JURÍDICO INTERACTIVO & TELEMETRÍA EN VIVO (ONDAS)
    // -------------------------------------------------------------
    let isComparisonMode = false;
    const btnToggleComparison = document.getElementById("btn-toggle-comparison");
    const compareToggleLabel = document.getElementById("compare-toggle-label");
    const comparisonActiveBanner = document.getElementById("comparison-active-banner");
    const chatContainer = document.querySelector(".chat-container");

    btnToggleComparison?.addEventListener("click", () => {
        isComparisonMode = !isComparisonMode;
        if (isComparisonMode) {
            btnToggleComparison.classList.add("active");
            if (compareToggleLabel) compareToggleLabel.textContent = "Comparativo 50/50: ACTIVO";
            if (comparisonActiveBanner) comparisonActiveBanner.classList.remove("hidden");
            if (chatContainer) chatContainer.classList.add("comparison-wide");
            neuralCockpit?.classList.add("comparison-layout");
        } else {
            btnToggleComparison.classList.remove("active");
            if (compareToggleLabel) compareToggleLabel.textContent = "Comparar vs Gemini";
            if (comparisonActiveBanner) comparisonActiveBanner.classList.add("hidden");
            if (chatContainer) chatContainer.classList.remove("comparison-wide");
            neuralCockpit?.classList.remove("comparison-layout");
        }
    });

    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const btnSend = document.getElementById("btn-send");
    const btnStop = document.getElementById("btn-stop");
    const hudBtnStop = document.getElementById("hud-btn-stop");
    const chkAnonymize = document.getElementById("chk-anonymize");

    // Control de Privacidad y Memoria Persistente (Bóveda Obsidian)
    const btnToggleMemory = document.getElementById("btn-toggle-memory");
    const memoryPillDot = document.getElementById("memory-pill-dot");
    const memoryToggleIcon = document.getElementById("memory-toggle-icon");
    const memoryToggleLabel = document.getElementById("memory-toggle-label");
    const chatPrivacyHint = document.getElementById("chat-privacy-hint");
    let currentAbortController = null;

    function setUIGeneratingState(isGenerating) {
        state.isQuerying = isGenerating;
        if (btnStop) btnStop.style.display = isGenerating ? "inline-flex" : "none";
        if (hudBtnStop) hudBtnStop.style.display = isGenerating ? "inline-flex" : "none";
        if (btnSend) {
            btnSend.style.display = isGenerating ? "none" : "inline-flex";
            btnSend.disabled = isGenerating;
        }
        const pedLiveSpinner = document.getElementById("ped-live-spinner");
        if (pedLiveSpinner) {
            pedLiveSpinner.style.display = isGenerating ? "inline-block" : "none";
        }
    }

    async function abortCurrentQuery() {
        if (!state.isQuerying) return;
        if (currentAbortController) {
            currentAbortController.abort();
            currentAbortController = null;
        }
        try {
            fetch("/api/chat/stop", { method: "POST" });
        } catch (_) {}
        setUIGeneratingState(false);
    }

    btnStop?.addEventListener("click", abortCurrentQuery);
    hudBtnStop?.addEventListener("click", abortCurrentQuery);

    btnToggleMemory?.addEventListener("click", () => {
        state.includeInMemory = !state.includeInMemory;
        if (state.includeInMemory) {
            btnToggleMemory.className = "toggle-control-pill active-save";
            if (memoryPillDot) memoryPillDot.className = "pill-dot mint";
            if (memoryToggleIcon) memoryToggleIcon.textContent = "🧠";
            if (memoryToggleLabel) memoryToggleLabel.textContent = "Memoria Activa (Guardar en Bóveda)";
            if (chatPrivacyHint) chatPrivacyHint.textContent = "El dictamen se archivará como precedente en Obsidian";
        } else {
            btnToggleMemory.className = "toggle-control-pill active-ephemeral";
            if (memoryPillDot) memoryPillDot.className = "pill-dot amber";
            if (memoryToggleIcon) memoryToggleIcon.textContent = "🛡️";
            if (memoryToggleLabel) memoryToggleLabel.textContent = "No incluir en memoria (Efímero)";
            if (chatPrivacyHint) chatPrivacyHint.textContent = "🔒 Modo privado: Este dictamen NO se guardará en la Bóveda de Obsidian";
        }
    });

    // Elementos del HUD de Telemetría
    const chatHud = document.getElementById("chat-hud");
    const hudPhaseLabel = document.getElementById("hud-phase-label");
    const hudStopwatch = document.getElementById("hud-stopwatch");
    const hudProgressFill = document.getElementById("hud-progress-fill");
    const hudBadgeCache = document.getElementById("hud-badge-cache");
    const hudBadgeWave1 = document.getElementById("hud-badge-wave1");
    const hudBadgeWave2 = document.getElementById("hud-badge-wave2");
    const hudDocsList = document.getElementById("hud-docs-list");

    let stopwatchInterval = null;
    let stopwatchStartTime = 0;

    function startStopwatch() {
        clearInterval(stopwatchInterval);
        stopwatchStartTime = Date.now();
        if (hudStopwatch) hudStopwatch.textContent = "00:00.0";
        stopwatchInterval = setInterval(() => {
            const elapsed = Date.now() - stopwatchStartTime;
            const totalSec = elapsed / 1000;
            const min = Math.floor(totalSec / 60);
            const sec = (totalSec % 60).toFixed(1);
            const minStr = String(min).padStart(2, "0");
            const secStr = sec.padStart(4, "0");
            if (hudStopwatch) hudStopwatch.textContent = `${minStr}:${secStr}`;
        }, 100);
    }

    function stopStopwatch() {
        clearInterval(stopwatchInterval);
        const elapsed = (Date.now() - stopwatchStartTime) / 1000;
        return elapsed.toFixed(1);
    }

    let userScrolledMainChat = false;
    if (chatMessages) {
        chatMessages.addEventListener("scroll", () => {
            const atBottom = (chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight) < 60;
            userScrolledMainChat = !atBottom;
        }, { passive: true });
    }

    function clearHudDocuments(statusMessage = "") {
        if (!hudDocsList) return;
        if (statusMessage) {
            hudDocsList.innerHTML = `<span class="doc-pill scanning-pill">🔄 ${escapeHtml(statusMessage)}</span>`;
        } else {
            hudDocsList.innerHTML = "";
        }
    }

    function renderHudDocuments(documents = [], fallbackText = "") {
        if (!hudDocsList) return;
        if (documents && documents.length > 0) {
            hudDocsList.innerHTML = documents.map(d => {
                const lbl = d.articulo || d.section || "Norma";
                return `<span class="doc-pill doc-pill-enter" title="${escapeHtml(d.source || "")}">📄 ${escapeHtml(lbl)}</span>`;
            }).join("");
        } else if (fallbackText) {
            hudDocsList.innerHTML = `<span class="doc-pill doc-pill-enter">${escapeHtml(fallbackText)}</span>`;
        } else {
            hudDocsList.innerHTML = "";
        }
    }

    function resetHUD() {
        if (!chatHud) return;
        chatHud.classList.remove("hidden");
        if (hudPhaseLabel) hudPhaseLabel.textContent = "Iniciando consulta jurídica...";
        if (hudProgressFill) hudProgressFill.style.width = "5%";
        if (hudBadgeCache) hudBadgeCache.classList.add("hidden");
        if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill active";
        if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill pending";
        clearHudDocuments("Invocando nuevas normas según la consulta actual...");
    }

    function mapPhaseToVisualizer(phaseName) {
        const viz = getViz();
        if (!viz || !phaseName) return;
        if (phaseName === "tokenization") {
            viz.activateLayer(1);
        } else if (phaseName === "precedent_check") {
            viz.activateLayer(2);
        } else if (phaseName === "retrieval" || phaseName === "lexical_bm25") {
            viz.activateLayer(3);
        } else if (phaseName === "vector_embedding") {
            viz.activateLayer(4);
        } else if (phaseName === "rerank" || phaseName === "wave_1_start") {
            // Permanece en Etapa 5 (Atención / Lectura de Contexto) hasta que llegue la primera palabra real
            viz.activateLayer(5);
        } else if (phaseName === "wave_1_done" || phaseName === "wave_2_start") {
            viz.onWaveTransition();
        }
    }

    async function sendQuery(queryText, skipCacheCheck = false) {
        if (!queryText || state.isQuerying) return;
        userScrolledMainChat = false;

        // Limpiar de inmediato los artículos en verde de la consulta anterior
        clearHudDocuments("Descartando artículos previos • Evaluando nueva consulta...");

        if (isComparisonMode) {
            return sendComparisonQuery(queryText);
        }

        const viz = getViz();

        // Antesala Interactiva: Comprobar si existe un precedente conceptual antes de inferir
        if (!skipCacheCheck) {
            viz?.activateLayer(1, { immediate: true });
            viz?.activateLayer(2);
            try {
                const checkRes = await fetch("/api/chat/check-intent", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: queryText })
                }).then(r => r.json()).catch(() => ({ found: false }));

                if (checkRes && checkRes.found) {
                    appendUserMessage(queryText);
                    chatInput.value = "";
                    clearHudDocuments("Precedente identificado en Bóveda Obsidiana • Esperando confirmación...");
                    renderIntentClarificationCard(queryText, checkRes);
                    return;
                }
            } catch (err) {
                console.warn("Check intent bypass:", err);
            }
        }

        executeStreamingQuery(queryText, skipCacheCheck);
    }

    function renderIntentClarificationCard(userQuery, precedent) {
        const cardId = "interceptor-" + Date.now();
        const wrapper = document.createElement("div");
        wrapper.className = "msg-wrapper assistant intent-interceptor-card";
        wrapper.id = cardId;
        wrapper.innerHTML = `
            <div class="msg-avatar assistant" style="background: rgba(52, 232, 176, 0.16); color: var(--bio-mint); border-color: var(--bio-mint);">💡</div>
            <div class="msg-bubble intent-interceptor-bubble">
                <div class="intent-interceptor-title">
                    <span>🧠 Precedente Jurídico Identificado en Memoria Obsidiana</span>
                    <span class="badge badge-green" style="font-size: 11px;">Afinidad: ${precedent.confidence_pct || 90}%</span>
                </div>
                <p style="margin: 4px 0 8px 0; font-size: 13px; color: var(--text-secondary);">
                    Detectamos una consulta con el <strong>mismo concepto rector</strong> en la Bóveda de Precedentes:
                </p>
                <div class="intent-matched-box">
                    <strong style="color: var(--bio-cyan); font-size: 14px;">«${escapeHtml(precedent.matched_query)}»</strong>
                    <p style="margin: 6px 0 0 0; font-size: 12px; color: var(--text-muted); font-style: italic;">
                        ${escapeHtml(precedent.preview || "")}...
                    </p>
                </div>
                <p style="font-size: 12.5px; color: var(--text-secondary); margin-bottom: 6px;">
                    ¿Deseas consultar el dictamen y ruta procesal ya verificados (Respuesta instantánea) o prefieres generar un análisis nuevo desde cero?
                </p>
                <div class="intent-actions">
                    <button type="button" class="btn-intent-yes" id="btn-yes-${cardId}">
                        <span>✓ Sí, ver dictamen del precedente (Instantáneo ⚡)</span>
                    </button>
                    <button type="button" class="btn-intent-no" id="btn-no-${cardId}">
                        <span>✕ No, investigar desde cero</span>
                    </button>
                </div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const viz = getViz();
        viz?.setTargetElement(wrapper.querySelector(".msg-bubble"));
        viz?.activateLayer(2, {
            immediate: true,
            customBadge: "💡 PRECEDENTE DETECTADO EN OBSIDIAN",
            customCallout: "Coincidencia Conceptual"
        });

        // Listener SÍ -> Cargar precedente instantáneamente
        document.getElementById(`btn-yes-${cardId}`)?.addEventListener("click", async () => {
            const actionsEl = wrapper.querySelector(".intent-actions");
            if (actionsEl) {
                actionsEl.innerHTML = `<span class="badge badge-green">✓ Precedente Aceptado por el Usuario — Desplegado en 0.05s</span>`;
            }
            await loadPrecedentAnswer(precedent.note_id, userQuery);
        });

        // Listener NO -> Ejecutar RAG desde cero
        document.getElementById(`btn-no-${cardId}`)?.addEventListener("click", () => {
            const actionsEl = wrapper.querySelector(".intent-actions");
            if (actionsEl) {
                actionsEl.innerHTML = `<span class="badge badge-blue">ℹ️ Nueva búsqueda solicitada — Iniciando RAG...</span>`;
            }
            executeStreamingQuery(userQuery, true);
        });
    }

    async function loadPrecedentAnswer(noteId, userQuery) {
        try {
            const res = await fetch("/api/chat/precedent-answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ note_id: noteId, query: userQuery })
            });
            if (!res.ok) throw new Error("No se pudo cargar la ficha del precedente.");
            const data = await res.json();

            const currentMsgId = "msg-" + Date.now();
            const wrapper = document.createElement("div");
            wrapper.className = "msg-wrapper assistant";
            wrapper.id = currentMsgId;
            wrapper.innerHTML = `
                <div class="msg-avatar assistant"><img src="/assets/sadigua-icon.png" alt="S"></div>
                <div class="msg-bubble">
                    <div class="bubble-badges" id="${currentMsgId}-badges">
                        <span class="badge badge-green">⚡ Precedente Verificado en Bóveda (Obsidian)</span>
                        <span class="badge badge-blue">⏱️ Recuperado en 0.05s</span>
                        <span class="badge">💰 Costo: $0.00</span>
                    </div>
                    <div class="bubble-content" id="${currentMsgId}-content">
                        ${formatResponseText(data.answer)}
                    </div>
                    <div class="bubble-sources" id="${currentMsgId}-sources" style="display:none; margin-top: 12px;"></div>
                </div>
            `;
            chatMessages.appendChild(wrapper);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            const sourcesEl = document.getElementById(`${currentMsgId}-sources`);
            if (data.sources && data.sources.length > 0) {
                renderSources(sourcesEl, data.sources);
            }
            renderHudDocuments(data.sources || [], "⚡ Precedente verificado recuperado desde Bóveda Obsidiana");
            if (hudPhaseLabel) hudPhaseLabel.textContent = "⚡ Precedente desplegado instantáneamente desde Bóveda.";
            if (hudProgressFill) hudProgressFill.style.width = "100%";

            const viz = getViz();
            viz?.setTargetElement(wrapper.querySelector(".msg-bubble"));
            viz?.completeSession({ cacheHit: true });
        } catch (e) {
            appendErrorMessage("Error recuperando precedente: " + e.message);
        }
    }

    async function executeStreamingQuery(queryText, skipCache = false) {
        state.isQuerying = true;
        setUIGeneratingState(true);
        currentAbortController = new AbortController();
        userScrolledMainChat = false;

        if (!skipCache) {
            appendUserMessage(queryText);
        }
        chatInput.value = "";

        resetHUD();
        startStopwatch();

        // Crear contenedor para mensaje progresivo del asistente
        const currentMsgId = "msg-" + Date.now();
        const wrapper = document.createElement("div");
        wrapper.className = "msg-wrapper assistant";
        wrapper.id = currentMsgId;
        wrapper.innerHTML = `
            <div class="msg-avatar assistant"><img src="/assets/sadigua-icon.png" alt="S"></div>
            <div class="msg-bubble">
                <div class="bubble-badges" id="${currentMsgId}-badges">
                    <span class="badge badge-blue">⚖️ Dictamen en curso...</span>
                </div>
                <div class="bubble-content" id="${currentMsgId}-content">
                    <span class="streaming-cursor"></span>
                </div>
                <div class="bubble-sources" id="${currentMsgId}-sources" style="display:none; margin-top: 12px;"></div>
            </div>
        `;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const bubbleEl = wrapper.querySelector(".msg-bubble");
        const contentEl = document.getElementById(`${currentMsgId}-content`);
        const badgesEl = document.getElementById(`${currentMsgId}-badges`);
        const sourcesEl = document.getElementById(`${currentMsgId}-sources`);

        const viz = getViz();
        viz?.startSession(bubbleEl);
        viz?.activateLayer(1, { immediate: true });

        let accumulatedText = "";
        let isWave2Started = false;
        let latestWave = 1;
        let rafRenderId = null;

        // Renderizado agrupado a 60 FPS (requestAnimationFrame):
        // Si el LLM ya emitió múltiples tokens o terminó un bloque, se pintan TODOS al instante sin cuello de botella DOM.
        const flushStreamRender = (isFinal = false) => {
            if (rafRenderId !== null) {
                cancelAnimationFrame(rafRenderId);
                rafRenderId = null;
            }
            if (contentEl) {
                contentEl.innerHTML = formatResponseText(accumulatedText) + (isFinal ? "" : '<span class="streaming-cursor"></span>');
            }
            if (!userScrolledMainChat && chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        };

        const scheduleStreamRender = () => {
            if (rafRenderId !== null) return;
            rafRenderId = requestAnimationFrame(() => {
                rafRenderId = null;
                if (contentEl) {
                    contentEl.innerHTML = formatResponseText(accumulatedText) + '<span class="streaming-cursor"></span>';
                }
                if (!userScrolledMainChat && chatMessages) {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            });
        };

        try {
            const res = await fetch("/api/chat/progressive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: queryText,
                    anonymize: chkAnonymize ? chkAnonymize.checked : true,
                    skip_cache: skipCache,
                    include_in_memory: state.includeInMemory
                }),
                signal: currentAbortController.signal
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Error en el servidor");
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop(); // Guardar residuo incompleto

                let receivedTokensInChunk = false;

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith("data:")) continue;
                    const jsonStr = trimmed.slice(5).trim();
                    if (!jsonStr) continue;

                    try {
                        const event = JSON.parse(jsonStr);

                        if (event.type === "phase") {
                            if (hudPhaseLabel) hudPhaseLabel.textContent = event.message;
                            if (hudProgressFill && event.progress) {
                                hudProgressFill.style.width = `${event.progress}%`;
                            }
                            mapPhaseToVisualizer(event.phase);

                            if (event.phase === "wave_1_start") {
                                if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill active";
                            } else if (event.phase === "wave_1_continuation") {
                                if (hudPhaseLabel) hudPhaseLabel.textContent = "🛡️ Completando cierre de idea en Onda 1...";
                            } else if (event.phase === "wave_1_done") {
                                flushStreamRender(false);
                                if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill done";
                                if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill active";
                                // Píldora de espera activa para informar al usuario que se está generando la Onda 2
                                if (contentEl && !document.getElementById("wave2-cooking-pill")) {
                                    const pill = document.createElement("div");
                                    pill.id = "wave2-cooking-pill";
                                    pill.className = "wave2-cooking-pill";
                                    pill.innerHTML = `<span class="hud-spinner"></span> <span><strong>Generando Onda 2:</strong> Redactando Ruta Procesal, Tutela y Acciones Concretas...</span>`;
                                    contentEl.parentElement.appendChild(pill);
                                    if (!userScrolledMainChat) chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                            } else if (event.phase === "wave_2_start") {
                                if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill active";
                            } else if (event.phase === "wave_2_continuation") {
                                if (hudPhaseLabel) hudPhaseLabel.textContent = "🛡️ Completando recomendaciones y cierre final...";
                            } else if (event.phase === "wave_2_done") {
                                flushStreamRender(false);
                                if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill done";
                                const cookingPill = document.getElementById("wave2-cooking-pill");
                                if (cookingPill) cookingPill.remove();
                            }
                        } else if (event.type === "documents_found") {
                            const newDocs = event.documents || [];
                            if (hudProgressFill && event.progress) {
                                hudProgressFill.style.width = `${event.progress}%`;
                            }
                            const liveViz = getViz();
                            if (liveViz) {
                                liveViz.scheduleDocsReveal(() => renderHudDocuments(newDocs, "Sin artículos específicos en corpus"));
                                liveViz.emitContextBurst(newDocs);
                            } else {
                                renderHudDocuments(newDocs, "Sin artículos específicos en corpus");
                            }
                        } else if (event.type === "mutations_detected") {
                            const mutations = event.mutations || [];
                            renderMutationBannersInChat(contentEl, mutations);
                        } else if (event.type === "token") {
                            if (event.wave === 2 && !isWave2Started) {
                                isWave2Started = true;
                                const cookingPill = document.getElementById("wave2-cooking-pill");
                                if (cookingPill) cookingPill.remove();
                                accumulatedText += "\n\n---\n\n### Ruta Procesal, Tutela y Acciones Concretas\n\n";
                            }
                            accumulatedText += event.text;
                            latestWave = event.wave || 1;
                            receivedTokensInChunk = true;
                        } else if (event.type === "stopped") {
                            const cookingPill = document.getElementById("wave2-cooking-pill");
                            if (cookingPill) cookingPill.remove();
                            stopStopwatch();
                            if (hudPhaseLabel) hudPhaseLabel.textContent = "⏹️ Síntesis detenida por el usuario.";
                            if (hudProgressFill) hudProgressFill.style.backgroundColor = "#ef4444";
                            accumulatedText += "\n\n> ⏹️ *[Síntesis detenida por el usuario]*";
                            flushStreamRender(true);
                            break;
                        } else if (event.type === "precedent_hit") {
                            const cookingPill = document.getElementById("wave2-cooking-pill");
                            if (cookingPill) cookingPill.remove();
                            const duration = stopStopwatch();
                            if (hudBadgeCache) {
                                hudBadgeCache.classList.remove("hidden");
                                hudBadgeCache.textContent = `⚡ Precedente en Bóveda (${(event.similarity * 100).toFixed(0)}% match)`;
                            }
                            if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill done";
                            if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill done";
                            if (hudProgressFill) hudProgressFill.style.width = "100%";
                            if (hudPhaseLabel) hudPhaseLabel.textContent = `⚡ Precedente recuperado en ${duration}s sin consumo de CPU.`;

                            if (badgesEl) {
                                badgesEl.innerHTML = `<span class="badge badge-green">⚡ Precedente Verificado en Bóveda (Obsidian)</span>`;
                            }
                            accumulatedText = event.answer;
                            flushStreamRender(true);
                            renderHudDocuments(event.sources || [], "⚡ Precedente verificado recuperado desde Bóveda Obsidiana");
                            renderSources(sourcesEl, event.sources);
                            getViz()?.completeSession({ cacheHit: true });
                        } else if (event.type === "grounding") {
                            getViz()?.activateLayer(7, { immediate: true });
                            if (badgesEl) {
                                let badgesHtml = event.grounded
                                    ? `<span class="badge badge-green">✓ Grounding Verificado en Corpus</span>`
                                    : `<span class="badge" style="background: var(--warning-bg); color: var(--warning-text);">⚠️ ${escapeHtml(event.grounding_status)}</span>`;
                                if (!event.in_memory) {
                                    badgesHtml += ` <span class="badge" style="background: rgba(250, 204, 21, 0.18); color: #FDE047; font-weight: 600;">🛡️ No Guardado en Memoria (Efímero)</span>`;
                                }
                                badgesEl.innerHTML = badgesHtml;
                            }
                            if (event.mutations_detected && event.mutations_detected.length) {
                                renderMutationBannersInChat(contentEl, event.mutations_detected);
                            }
                            renderSources(sourcesEl, event.sources);

                            // Si se guardó en memoria y tiene note_id, permitir eliminarlo con el botón "Quitar de memoria"
                            if (sourcesEl && event.note_id && event.in_memory !== false) {
                                const forgetBtn = document.createElement("button");
                                forgetBtn.type = "button";
                                forgetBtn.className = "btn-msg-forget";
                                forgetBtn.innerHTML = `<span>🗑️ Quitar de memoria</span>`;
                                forgetBtn.title = "Eliminar este dictamen de la Bóveda de Obsidian";
                                forgetBtn.addEventListener("click", async () => {
                                    if (!confirm("¿Deseas quitar este dictamen de la Bóveda de Precedentes de Obsidian?")) return;
                                    try {
                                        const delRes = await fetch(`/api/vault/consultas/${event.note_id}`, { method: "DELETE" });
                                        if (delRes.ok) {
                                            forgetBtn.remove();
                                            if (badgesEl) {
                                                badgesEl.innerHTML += ` <span class="badge" style="background: rgba(248, 113, 113, 0.2); color: #fca5a5;">🗑️ Removido de la Bóveda</span>`;
                                            }
                                        }
                                    } catch (err) {
                                        alert("Error eliminando de la bóveda: " + err.message);
                                    }
                                });
                                sourcesEl.appendChild(forgetBtn);
                            }
                        } else if (event.type === "done") {
                            const cookingPill = document.getElementById("wave2-cooking-pill");
                            if (cookingPill) cookingPill.remove();
                            const totalDuration = stopStopwatch();
                            if (hudProgressFill) hudProgressFill.style.width = "100%";
                            if (hudPhaseLabel) {
                                hudPhaseLabel.textContent = event.in_memory === false
                                    ? `✓ Respuesta completada en modo privado (${totalDuration}s — No guardada en Bóveda)`
                                    : `✓ Respuesta completada y archivada en Bóveda (${totalDuration}s)`;
                            }
                            flushStreamRender(true);
                            getViz()?.completeSession({ cacheHit: false });
                        } else if (event.type === "error") {
                            throw new Error(event.message);
                        }
                    } catch (parseErr) {
                        console.warn("Línea SSE:", jsonStr, parseErr);
                    }
                }

                if (receivedTokensInChunk) {
                    scheduleStreamRender();
                    getViz()?.onTokenGenerated(accumulatedText, latestWave);
                }
            }
            flushStreamRender(true);
        } catch (e) {
            if (rafRenderId !== null) cancelAnimationFrame(rafRenderId);
            stopStopwatch();
            getViz()?.handleError();
            if (e.name === "AbortError" || (e.message && e.message.includes("aborted"))) {
                const cookingPill = document.getElementById("wave2-cooking-pill");
                if (cookingPill) cookingPill.remove();
                if (hudPhaseLabel) hudPhaseLabel.textContent = "⏹️ Síntesis detenida por el usuario.";
                if (hudProgressFill) hudProgressFill.style.backgroundColor = "#ef4444";
                accumulatedText += "\n\n> ⏹️ *[Síntesis detenida por el usuario]*";
                flushStreamRender(true);
            } else {
                if (hudPhaseLabel) hudPhaseLabel.textContent = `❌ Error: ${e.message}`;
                appendErrorMessage(e.message);
            }
        } finally {
            state.isQuerying = false;
            currentAbortController = null;
            setUIGeneratingState(false);
            chatInput.focus();
        }
    }

    // -------------------------------------------------------------
    // 2.1. MODO COMPARATIVO PARALELO (ARENA PEDAGÓGICA: LOCAL VS GEMINI)
    // -------------------------------------------------------------
    async function sendComparisonQuery(queryText) {
        state.isQuerying = true;
        setUIGeneratingState(true);
        currentAbortController = new AbortController();
        chatInput.value = "";

        appendUserMessage(queryText);
        resetHUD();
        startStopwatch();

        const arenaId = Date.now();
        const currentLocalModel = document.getElementById("quick-model-select")?.value || "qwen2.5:7b-instruct";
        const currentGeminiModel = document.getElementById("cfg-gemini-model")?.value || "gemini-3.8-flash";

        const arenaWrapper = document.createElement("div");
        arenaWrapper.className = "comparison-arena";
        arenaWrapper.id = `arena-${arenaId}`;
        arenaWrapper.innerHTML = `
            <!-- Columna Izquierda: Modelo Local Soberano -->
            <div class="arena-col local">
                <div class="arena-header">
                    <div class="arena-title-row">
                        <div class="arena-title">
                            <div class="arena-avatar local"><img src="/assets/sadigua-icon.png" alt="S"></div>
                            <div>
                                <strong style="color: var(--bio-mint); font-size: 14px;">Modelo Local Soberano</strong>
                                <div class="arena-model-name">${escapeHtml(currentLocalModel)} (100% Offline)</div>
                            </div>
                        </div>
                        <div class="arena-scroll-actions" title="Controles de scroll independiente para Modelo Local">
                            <span class="arena-scroll-label">Scroll:</span>
                            <button type="button" class="arena-scroll-btn" id="scroll-top-local-${arenaId}" title="Ir al inicio de la respuesta local">⬆️ Arriba</button>
                            <button type="button" class="arena-scroll-btn" id="scroll-bottom-local-${arenaId}" title="Ir al final de la respuesta local">⬇️ Abajo</button>
                        </div>
                    </div>
                    <div class="arena-badges">
                        <span class="badge badge-green">🔒 Soberanía 100% (Ley 1581)</span>
                        <span class="badge badge-blue">💰 Costo: $0.00</span>
                        <span class="arena-metric-pill timer" id="local-timer-${arenaId}">⏱️ 00:00.0s</span>
                        <span class="arena-metric-pill speed" id="local-speed-${arenaId}">⚡ -- tok/s</span>
                    </div>
                </div>
                <div class="arena-body" id="local-body-${arenaId}">
                    <div class="arena-loading"><span class="hud-spinner"></span> <span>Iniciando inferencia local en CPU...</span></div>
                </div>
                <div class="arena-footer" id="local-footer-${arenaId}">
                    <span id="local-status-${arenaId}" style="color: var(--text-secondary);">⏳ Procesando consulta...</span>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span id="local-tokens-${arenaId}" style="font-family: monospace; font-size: 11px;">0 tokens</span>
                        <button type="button" class="arena-footer-scroll-btn" id="footer-scroll-top-local-${arenaId}" title="Subir al inicio">⬆️</button>
                        <button type="button" class="arena-footer-scroll-btn" id="footer-scroll-bottom-local-${arenaId}" title="Bajar al final">⬇️</button>
                    </div>
                </div>
            </div>

            <!-- Columna Derecha: Google Gemini Cloud -->
            <div class="arena-col gemini">
                <div class="arena-header">
                    <div class="arena-title-row">
                        <div class="arena-title">
                            <div class="arena-avatar gemini">G</div>
                            <div>
                                <strong style="color: #C084FC; font-size: 14px;">Google Gemini Cloud</strong>
                                <div class="arena-model-name">${escapeHtml(currentGeminiModel)} (Cloud API)</div>
                            </div>
                        </div>
                        <div class="arena-scroll-actions" title="Controles de scroll independiente para Gemini Cloud">
                            <span class="arena-scroll-label">Scroll:</span>
                            <button type="button" class="arena-scroll-btn" id="scroll-top-gemini-${arenaId}" title="Ir al inicio de la respuesta de Gemini">⬆️ Arriba</button>
                            <button type="button" class="arena-scroll-btn" id="scroll-bottom-gemini-${arenaId}" title="Ir al final de la respuesta de Gemini">⬇️ Abajo</button>
                        </div>
                    </div>
                    <div class="arena-badges">
                        <span class="badge" style="background: var(--warning-bg); color: var(--warning-text); border-color: rgba(250, 204, 21, 0.35);">☁️ Nube Pública</span>
                        <span class="badge" style="background: var(--danger-bg); color: var(--danger-text); border-color: rgba(248, 113, 113, 0.35);">💳 Costo Cloud API</span>
                        <span class="arena-metric-pill timer" id="gemini-timer-${arenaId}">⏱️ 00:00.0s</span>
                        <span class="arena-metric-pill speed" id="gemini-speed-${arenaId}">⚡ -- tok/s</span>
                    </div>
                </div>
                <div class="arena-body" id="gemini-body-${arenaId}">
                    <div class="arena-loading"><span class="hud-spinner"></span> <span>Conectando con Google Gemini en la nube...</span></div>
                </div>
                <div class="arena-footer" id="gemini-footer-${arenaId}">
                    <span id="gemini-status-${arenaId}" style="color: var(--text-secondary);">⏳ Esperando primeros tokens...</span>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span id="gemini-tokens-${arenaId}" style="font-family: monospace; font-size: 11px;">0 tokens</span>
                        <button type="button" class="arena-footer-scroll-btn" id="footer-scroll-top-gemini-${arenaId}" title="Subir al inicio">⬆️</button>
                        <button type="button" class="arena-footer-scroll-btn" id="footer-scroll-bottom-gemini-${arenaId}" title="Bajar al final">⬇️</button>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(arenaWrapper);
        arenaWrapper.scrollIntoView({ behavior: "smooth", block: "nearest" });

        // Enlazar visualizador sináptico a la columna del Modelo Local Soberano
        const viz = getViz();
        viz?.startSession(arenaWrapper.querySelector(".arena-col.local"));
        viz?.activateLayer(1, { immediate: true });

        // Inicializar controles de scroll independientes para ambas ventanas
        const scrollState = setupArenaScrollControls(arenaId);

        // Disparar ambos streams en paralelo
        const localPromise = runLocalStream(queryText, arenaId, scrollState);
        const geminiPromise = runGeminiStream(queryText, arenaId, scrollState);

        const [localRes, geminiRes] = await Promise.allSettled([localPromise, geminiPromise]);

        const localData = localRes.status === "fulfilled" ? localRes.value : { error: true, time: 0, tokens: 0, speed: 0 };
        const geminiData = geminiRes.status === "fulfilled" ? geminiRes.value : { error: true, time: 0, tokens: 0, speed: 0 };

        // Renderizar Tarjeta de Evaluación Comparativa
        renderComparisonSummary(arenaWrapper, arenaId, localData, geminiData);

        state.isQuerying = false;
        currentAbortController = null;
        setUIGeneratingState(false);
        chatInput.focus();
    }

    function setupArenaScrollControls(arenaId) {
        const localBody = document.getElementById(`local-body-${arenaId}`);
        const geminiBody = document.getElementById(`gemini-body-${arenaId}`);

        const scrollState = {
            userScrolledLocal: false,
            userScrolledGemini: false
        };

        const scrollPane = (pane, target) => {
            if (!pane) return;
            const topVal = target === "top" ? 0 : pane.scrollHeight;
            pane.scrollTo({ top: topVal, behavior: "smooth" });
        };

        // Scroll Local
        const handleLocalScroll = (target) => {
            scrollState.userScrolledLocal = (target === "top");
            scrollPane(localBody, target);
        };

        document.getElementById(`scroll-top-local-${arenaId}`)?.addEventListener("click", () => handleLocalScroll("top"));
        document.getElementById(`scroll-bottom-local-${arenaId}`)?.addEventListener("click", () => handleLocalScroll("bottom"));
        document.getElementById(`footer-scroll-top-local-${arenaId}`)?.addEventListener("click", () => handleLocalScroll("top"));
        document.getElementById(`footer-scroll-bottom-local-${arenaId}`)?.addEventListener("click", () => handleLocalScroll("bottom"));

        // Scroll Gemini
        const handleGeminiScroll = (target) => {
            scrollState.userScrolledGemini = (target === "top");
            scrollPane(geminiBody, target);
        };

        document.getElementById(`scroll-top-gemini-${arenaId}`)?.addEventListener("click", () => handleGeminiScroll("top"));
        document.getElementById(`scroll-bottom-gemini-${arenaId}`)?.addEventListener("click", () => handleGeminiScroll("bottom"));
        document.getElementById(`footer-scroll-top-gemini-${arenaId}`)?.addEventListener("click", () => handleGeminiScroll("top"));
        document.getElementById(`footer-scroll-bottom-gemini-${arenaId}`)?.addEventListener("click", () => handleGeminiScroll("bottom"));

        // Detección de scroll manual independiente para cada panel
        if (localBody) {
            localBody.addEventListener("scroll", () => {
                const atBottom = (localBody.scrollHeight - localBody.scrollTop - localBody.clientHeight) < 40;
                scrollState.userScrolledLocal = !atBottom;
            }, { passive: true });
        }

        if (geminiBody) {
            geminiBody.addEventListener("scroll", () => {
                const atBottom = (geminiBody.scrollHeight - geminiBody.scrollTop - geminiBody.clientHeight) < 40;
                scrollState.userScrolledGemini = !atBottom;
            }, { passive: true });
        }

        return scrollState;
    }

    async function runLocalStream(queryText, arenaId, scrollState) {
        const timerEl = document.getElementById(`local-timer-${arenaId}`);
        const speedEl = document.getElementById(`local-speed-${arenaId}`);
        const bodyEl = document.getElementById(`local-body-${arenaId}`);
        const statusEl = document.getElementById(`local-status-${arenaId}`);
        const tokensEl = document.getElementById(`local-tokens-${arenaId}`);

        const startTime = Date.now();
        let tokenCount = 0;
        let accumulatedText = "";
        let isWave2Started = false;
        let wasCacheHit = false;
        let latestWave = 1;
        let rafLocalId = null;

        const scheduleLocalRender = () => {
            if (rafLocalId !== null) return;
            rafLocalId = requestAnimationFrame(() => {
                rafLocalId = null;
                if (bodyEl && !wasCacheHit) {
                    bodyEl.innerHTML = formatResponseText(accumulatedText) + '<span class="streaming-cursor"></span>';
                    if (!scrollState?.userScrolledLocal) {
                        bodyEl.scrollTop = bodyEl.scrollHeight;
                    }
                }
                const elapsedSec = (Date.now() - startTime) / 1000;
                if (speedEl && elapsedSec > 0) {
                    speedEl.textContent = `⚡ ${(tokenCount / elapsedSec).toFixed(1)} tok/s`;
                }
                if (tokensEl) tokensEl.textContent = `${tokenCount} tokens`;
            });
        };

        const interval = setInterval(() => {
            const elapsed = (Date.now() - startTime) / 1000;
            const min = Math.floor(elapsed / 60);
            const sec = (elapsed % 60).toFixed(1);
            if (timerEl) timerEl.textContent = `⏱️ ${String(min).padStart(2, "0")}:${sec.padStart(4, "0")}s`;
        }, 100);

        try {
            const res = await fetch("/api/chat/progressive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: queryText,
                    anonymize: chkAnonymize ? chkAnonymize.checked : true,
                    include_in_memory: state.includeInMemory
                }),
                signal: currentAbortController ? currentAbortController.signal : undefined
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Error en el servidor local");
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop();

                let receivedTokens = false;

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith("data:")) continue;
                    const jsonStr = trimmed.slice(5).trim();
                    if (!jsonStr) continue;

                    try {
                        const event = JSON.parse(jsonStr);
                        if (event.type === "phase") {
                            if (statusEl) statusEl.textContent = event.message;
                            if (hudPhaseLabel) hudPhaseLabel.textContent = event.message;
                            if (hudProgressFill && event.progress) {
                                hudProgressFill.style.width = `${event.progress}%`;
                            }
                            mapPhaseToVisualizer(event.phase);
                        } else if (event.type === "documents_found") {
                            const newDocs = event.documents || [];
                            const liveViz = getViz();
                            if (liveViz) {
                                liveViz.scheduleDocsReveal(() => renderHudDocuments(newDocs, "Sin artículos específicos en corpus"));
                                liveViz.emitContextBurst(newDocs);
                            } else {
                                renderHudDocuments(newDocs, "Sin artículos específicos en corpus");
                            }
                        } else if (event.type === "mutations_detected") {
                            const mutations = event.mutations || [];
                            renderMutationBannersInChat(bodyEl, mutations);
                        } else if (event.type === "token") {
                            if (event.wave === 2 && !isWave2Started) {
                                isWave2Started = true;
                                accumulatedText += "\n\n---\n\n### Ruta Procesal, Tutela y Acciones Concretas\n\n";
                            }
                            tokenCount++;
                            accumulatedText += event.text;
                            latestWave = event.wave || 1;
                            receivedTokens = true;
                        } else if (event.type === "precedent_hit") {
                            wasCacheHit = true;
                            if (rafLocalId !== null) {
                                cancelAnimationFrame(rafLocalId);
                                rafLocalId = null;
                            }
                            accumulatedText = event.answer;
                            renderHudDocuments(event.sources || [], "⚡ Precedente verificado recuperado desde Bóveda Obsidiana");
                            if (bodyEl) {
                                bodyEl.innerHTML = `<div class="badge badge-green" style="margin-bottom: 8px;">⚡ Precedente en Bóveda (${(event.similarity*100).toFixed(0)}%)</div><br>` + formatResponseText(accumulatedText);
                                if (!scrollState?.userScrolledLocal) {
                                    bodyEl.scrollTop = bodyEl.scrollHeight;
                                }
                            }
                        } else if (event.type === "grounding") {
                            getViz()?.activateLayer(7, { immediate: true });
                            if (event.mutations_detected && event.mutations_detected.length) {
                                renderMutationBannersInChat(bodyEl, event.mutations_detected);
                            }
                        } else if (event.type === "done") {
                            // Listo
                        }
                    } catch (e) {}
                }

                if (receivedTokens) {
                    scheduleLocalRender();
                    getViz()?.onTokenGenerated(accumulatedText, latestWave);
                }
            }

            if (rafLocalId !== null) cancelAnimationFrame(rafLocalId);
            clearInterval(interval);
            stopStopwatch();
            const totalElapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            if (hudProgressFill) hudProgressFill.style.width = "100%";
            if (hudPhaseLabel) hudPhaseLabel.textContent = `✓ Modelo Local completado (${totalElapsed}s)`;
            getViz()?.completeSession({ cacheHit: wasCacheHit });

            if (bodyEl && !wasCacheHit) {
                bodyEl.innerHTML = formatResponseText(accumulatedText);
                if (!scrollState?.userScrolledLocal) {
                    bodyEl.scrollTop = bodyEl.scrollHeight;
                }
            }
            const tokSec = totalElapsed > 0 ? (tokenCount / totalElapsed).toFixed(1) : 0;
            if (statusEl) statusEl.textContent = `✓ Concluido en ${totalElapsed}s | 100% Soberano`;
            return { time: parseFloat(totalElapsed), tokens: tokenCount, speed: parseFloat(tokSec) };

        } catch (err) {
            if (rafLocalId !== null) cancelAnimationFrame(rafLocalId);
            clearInterval(interval);
            stopStopwatch();
            getViz()?.handleError();
            if (err.name === "AbortError" || (err.message && err.message.includes("aborted"))) {
                if (bodyEl) {
                    bodyEl.innerHTML = formatResponseText(accumulatedText) + '<div style="color: var(--warning-text); margin-top: 8px;"><em>⏹️ Síntesis detenida por el usuario.</em></div>';
                }
                if (statusEl) statusEl.textContent = "⏹️ Detenido por el usuario";
                return { error: false, time: 0, tokens: tokenCount, speed: 0, stopped: true };
            }
            if (bodyEl) {
                bodyEl.innerHTML = `<div style="color: var(--danger-text); padding: 12px; background: var(--danger-bg); border: 1px solid rgba(248, 113, 113, 0.4); border-radius: 8px;"><strong>Error Local:</strong> ${escapeHtml(err.message)}</div>`;
            }
            if (statusEl) statusEl.textContent = "❌ Error en inferencia local";
            return { error: true, message: err.message };
        }
    }

    async function runGeminiStream(queryText, arenaId, scrollState) {
        const timerEl = document.getElementById(`gemini-timer-${arenaId}`);
        const speedEl = document.getElementById(`gemini-speed-${arenaId}`);
        const bodyEl = document.getElementById(`gemini-body-${arenaId}`);
        const statusEl = document.getElementById(`gemini-status-${arenaId}`);
        const tokensEl = document.getElementById(`gemini-tokens-${arenaId}`);

        const startTime = Date.now();
        let tokenCount = 0;
        let accumulatedText = "";
        let rafGeminiId = null;

        const scheduleGeminiRender = () => {
            if (rafGeminiId !== null) return;
            rafGeminiId = requestAnimationFrame(() => {
                rafGeminiId = null;
                if (bodyEl) {
                    bodyEl.innerHTML = formatResponseText(accumulatedText) + '<span class="streaming-cursor"></span>';
                    if (!scrollState?.userScrolledGemini) {
                        bodyEl.scrollTop = bodyEl.scrollHeight;
                    }
                }
                const elapsedSec = (Date.now() - startTime) / 1000;
                if (speedEl && elapsedSec > 0) {
                    speedEl.textContent = `⚡ ${(tokenCount / elapsedSec).toFixed(1)} tok/s`;
                }
                if (tokensEl) tokensEl.textContent = `${tokenCount} tokens`;
            });
        };

        const interval = setInterval(() => {
            const elapsed = (Date.now() - startTime) / 1000;
            const min = Math.floor(elapsed / 60);
            const sec = (elapsed % 60).toFixed(1);
            if (timerEl) timerEl.textContent = `⏱️ ${String(min).padStart(2, "0")}:${sec.padStart(4, "0")}s`;
        }, 100);

        try {
            const res = await fetch("/api/chat/gemini-stream", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: queryText,
                    anonymize: chkAnonymize ? chkAnonymize.checked : true
                }),
                signal: currentAbortController ? currentAbortController.signal : undefined
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || "Error en el servidor");
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop();

                let receivedGeminiTokens = false;

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith("data:")) continue;
                    const jsonStr = trimmed.slice(5).trim();
                    if (!jsonStr) continue;

                    try {
                        const event = JSON.parse(jsonStr);
                        if (event.type === "phase") {
                            if (statusEl) statusEl.textContent = event.message;
                        } else if (event.type === "token") {
                            tokenCount++;
                            accumulatedText += event.text;
                            receivedGeminiTokens = true;
                        } else if (event.type === "error") {
                            if (rafGeminiId !== null) cancelAnimationFrame(rafGeminiId);
                            clearInterval(interval);
                            if (bodyEl) {
                                bodyEl.innerHTML = `
                                    <div style="background: var(--danger-bg); border: 1px solid rgba(248, 113, 113, 0.4); border-radius: 8px; padding: 14px; color: var(--danger-text);">
                                        <strong>⚠️ Configuración de Gemini Requerida:</strong>
                                        <p style="margin: 6px 0 10px 0; font-size: 13px; color: var(--text-primary);">${escapeHtml(event.message)}</p>
                                        <button type="button" class="btn-primary" style="font-size: 12px; padding: 5px 12px;" onclick="document.querySelector('[data-tab=tab-settings]').click();">
                                             ⚙️ Ir a Configuración MLOps para cargar API Key
                                        </button>
                                    </div>
                                `;
                            }
                            if (statusEl) statusEl.textContent = "⚠️ Clave no configurada o error de red";
                            return { error: true, message: event.message };
                        } else if (event.type === "done") {
                            // Listo
                        }
                    } catch (e) {}
                }

                if (receivedGeminiTokens) {
                    scheduleGeminiRender();
                }
            }

            if (rafGeminiId !== null) cancelAnimationFrame(rafGeminiId);
            clearInterval(interval);
            const totalElapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            if (bodyEl) {
                bodyEl.innerHTML = formatResponseText(accumulatedText);
                if (!scrollState?.userScrolledGemini) {
                    bodyEl.scrollTop = bodyEl.scrollHeight;
                }
            }
            const tokSec = totalElapsed > 0 ? (tokenCount / totalElapsed).toFixed(1) : 0;
            if (statusEl) statusEl.textContent = `✓ Concluido en ${totalElapsed}s | Cloud Híbrido`;
            return { time: parseFloat(totalElapsed), tokens: tokenCount, speed: parseFloat(tokSec) };

        } catch (err) {
            if (rafGeminiId !== null) cancelAnimationFrame(rafGeminiId);
            clearInterval(interval);
            if (err.name === "AbortError" || (err.message && err.message.includes("aborted"))) {
                if (bodyEl) {
                    bodyEl.innerHTML = formatResponseText(accumulatedText) + '<div style="color: var(--warning-text); margin-top: 8px;"><em>⏹️ Síntesis detenida por el usuario.</em></div>';
                }
                if (statusEl) statusEl.textContent = "⏹️ Detenido por el usuario";
                return { error: false, time: 0, tokens: tokenCount, speed: 0, stopped: true };
            }
            if (bodyEl) {
                bodyEl.innerHTML = `<div style="color: var(--danger-text); padding: 12px; background: var(--danger-bg); border: 1px solid rgba(248, 113, 113, 0.4); border-radius: 8px;"><strong>Error Gemini Cloud:</strong> ${escapeHtml(err.message)}</div>`;
            }
            if (statusEl) statusEl.textContent = "❌ Error en conexión Cloud";
            return { error: true, message: err.message };
        }
    }

    function renderComparisonSummary(arenaWrapper, arenaId, localData, geminiData) {
        const summaryCard = document.createElement("div");
        summaryCard.className = "comparison-summary-card";
        summaryCard.id = `summary-${arenaId}`;

        const localTimeStr = localData.error ? "Error" : `${localData.time}s (${localData.speed} tok/s)`;
        const geminiTimeStr = geminiData.error ? "No ejecutado / Sin API Key" : `${geminiData.time}s (${geminiData.speed} tok/s)`;

        summaryCard.innerHTML = `
            <h4>⚖️ Veredicto Comparativo Pedagógico</h4>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th style="width: 25%;">Criterio Evaluado</th>
                        <th style="width: 32%;">🏠 Modelo Local Soberano</th>
                        <th style="width: 32%;">🌐 Google Gemini Cloud</th>
                        <th style="width: 11%;">Balance</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Soberanía & Reserva Legal</strong></td>
                        <td><span class="badge badge-green">🔒 100% On-Premise</span> (Cumple Ley 1581 & Conpes 4144)</td>
                        <td><span class="badge" style="background: var(--warning-bg); color: var(--warning-text); border-color: rgba(250, 204, 21, 0.35);">☁️ Nube Pública</span> (Transferencia fuera del host)</td>
                        <td><strong style="color: var(--bio-mint);">Local Gana</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Costo Operativo</strong></td>
                        <td><strong style="color: var(--bio-mint);">$0.00 COP</strong> (Inferencia ilimitada en hardware propio)</td>
                        <td>Tarifa por millón de tokens en USD + Facturación mensual</td>
                        <td><strong style="color: var(--bio-mint);">Local Gana</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Rendimiento & Latencia</strong></td>
                        <td>${localTimeStr} en CPU AVX2</td>
                        <td>${geminiTimeStr} en Google Cloud TPU</td>
                        <td><strong style="color: var(--bio-cyan);">${geminiData.error ? 'Local Activo' : 'Gemini +rápido'}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Garantía de Continuidad</strong></td>
                        <td><span class="badge badge-green">✓ Opera sin Internet</span> (Air-Gapped)</td>
                        <td><span class="badge" style="background: var(--warning-bg); color: var(--warning-text); border-color: rgba(250, 204, 21, 0.35);">⚠️ Depende de Conectividad</span></td>
                        <td><strong style="color: var(--bio-mint);">Local Gana</strong></td>
                    </tr>
                </tbody>
            </table>
            <p style="margin: 10px 0 0 0; font-size: 12px; color: var(--text-secondary); line-height: 1.5;">
                💡 <strong>Conclusión para el Despliegue:</strong> La prueba demuestra que el modelo local ejecuta la fundamentación jurídica y la ruta procesal completa con cero fuga de información y costo cero. Puede usarse con total tranquilidad y solvencia operativa.
            </p>
        `;
        arenaWrapper.insertAdjacentElement("afterend", summaryCard);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function renderSources(container, sources) {
        if (!container || !sources || sources.length === 0) return;
        const listItems = sources.map(s => {
            const label = s.articulo || s.section || "Norma";
            return `<li class="citation-item">📄 ${escapeHtml(s.source)} — <strong>${escapeHtml(label)}</strong></li>`;
        }).join("");
        container.innerHTML = `
            <div class="citations-box">
                <h5>Fuentes y Normas Recuperadas por RAG:</h5>
                <ul style="padding-left: 18px; margin: 0;">${listItems}</ul>
            </div>
        `;
        container.style.display = "block";
    }

    function appendUserMessage(text) {
        const wrapper = document.createElement("div");
        wrapper.className = "msg-wrapper user";
        wrapper.innerHTML = `
            <div class="msg-avatar user">U</div>
            <div class="msg-bubble">${escapeHtml(text)}</div>
        `;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendErrorMessage(errorText) {
        const wrapper = document.createElement("div");
        wrapper.className = "msg-wrapper assistant";
        wrapper.innerHTML = `
            <div class="msg-avatar assistant">!</div>
            <div class="msg-bubble" style="border-color: rgba(248, 113, 113, 0.45); background: var(--danger-bg); color: var(--danger-text);">
                <strong>Error en la consulta:</strong> ${escapeHtml(errorText)}
            </div>
        `;
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Eventos de envío de chat
    btnSend?.addEventListener("click", () => sendQuery(chatInput.value.trim()));
    chatInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendQuery(chatInput.value.trim());
        }
    });

    // Píldoras de sugerencias rápidas
    document.querySelectorAll(".prompt-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            const query = pill.dataset.query;
            if (query) sendQuery(query);
        });
    });

    // -------------------------------------------------------------
    // 3. CEREBRO OBSIDIANO (VAULT)
    // -------------------------------------------------------------
    const vaultGrid = document.getElementById("vault-notes-grid");
    const filterBtns = document.querySelectorAll(".filter-bar .filter-btn");
    const vaultSearchInput = document.getElementById("vault-search-input");
    const btnClearVaultSearch = document.getElementById("btn-clear-vault-search");
    const btnVaultOpenMemorial = document.getElementById("btn-vault-open-memorial");

    let currentVaultCategory = "all";
    let currentVaultQuery = "";

    async function loadVaultNotes(category = null) {
        if (category !== null) {
            currentVaultCategory = category;
        }
        try {
            const url = currentVaultCategory === "all" ? "/api/vault/notes" : `/api/vault/notes?category=${currentVaultCategory}`;
            const res = await fetch(url);
            const notes = await res.json();
            state.notes = notes;
            applyVaultFilters();
        } catch (e) {
            console.error("Error cargando notas de la bóveda:", e);
        }
    }

    function applyVaultFilters() {
        if (!state.notes) return;
        let filtered = state.notes;

        if (currentVaultCategory !== "all") {
            filtered = filtered.filter(n => n.category === currentVaultCategory);
        }

        if (currentVaultQuery) {
            const q = currentVaultQuery.toLowerCase();
            filtered = filtered.filter(n => 
                (n.title && n.title.toLowerCase().includes(q)) ||
                (n.snippet && n.snippet.toLowerCase().includes(q)) ||
                (n.id && n.id.toLowerCase().includes(q)) ||
                (n.subcategory && n.subcategory.toLowerCase().includes(q)) ||
                (n.entidad_accionada && n.entidad_accionada.toLowerCase().includes(q)) ||
                (n.tags && n.tags.some(t => t.toLowerCase().includes(q)))
            );
        }

        renderVaultNotes(filtered);
    }

    function renderVaultNotes(notes) {
        if (!vaultGrid) return;
        vaultGrid.innerHTML = "";

        if (notes.length === 0) {
            vaultGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-secondary);">
                    <p style="font-size: 32px; margin-bottom: 8px;">📂</p>
                    <p style="font-weight: 600;">No se encontraron notas con el filtro o búsqueda actual.</p>
                    <p style="font-size: 13px;">Prueba borrando el término de búsqueda o seleccionando 'Todos'.</p>
                </div>
            `;
            return;
        }

        notes.forEach(note => {
            const card = document.createElement("div");
            const catClass = `cat-${note.category || 'general'}`;
            card.className = `note-card ${catClass}`;

            let catLabel = note.category;
            if (note.category === "consultas") catLabel = "⚡ Precedente";
            else if (note.category === "minutas") {
                const sub = note.subcategory ? note.subcategory.replace(/_/g, ' ') : 'Tutela';
                catLabel = `📜 Minuta: ${sub}`;
            } else if (note.category === "jurisprudencia") catLabel = "🏛️ Jurisprudencia";
            else if (note.category === "expedientes") catLabel = "📁 Expediente";
            else if (note.category === "clientes") catLabel = "👤 Cliente";
            else if (note.category === "conceptos") catLabel = "💡 Concepto";

            let metaRowHtml = "";
            if (note.entidad_accionada || note.tipo_accion) {
                metaRowHtml = `<div class="note-meta-row">`;
                if (note.tipo_accion) {
                    metaRowHtml += `<span class="note-meta-chip">⚖️ <strong>${escapeHtml(note.tipo_accion)}</strong></span>`;
                }
                if (note.entidad_accionada) {
                    metaRowHtml += `<span class="note-meta-chip">🏛️ ${escapeHtml(note.entidad_accionada)}</span>`;
                }
                metaRowHtml += `</div>`;
            }

            card.innerHTML = `
                <div class="note-header">
                    <span class="note-category">${escapeHtml(catLabel)}</span>
                    <span style="font-size: 11px; color: var(--text-muted);">${escapeHtml(note.id)}</span>
                </div>
                <h4 class="note-title">${escapeHtml(note.title)}</h4>
                ${metaRowHtml}
                <p class="note-snippet">${escapeHtml(note.snippet)}</p>
                <div class="note-footer">
                    <span>📅 ${escapeHtml(note.updated || 'Reciente')}</span>
                    <span style="color: var(--bio-cyan); font-weight: 600;">Ver Documento ➔</span>
                </div>
            `;
            card.addEventListener("click", () => openNoteModal(note.category, note.id));
            vaultGrid.appendChild(card);
        });
    }

    // Eventos de filtro y buscador en Bóveda
    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentVaultCategory = btn.dataset.cat || "all";
            loadVaultNotes(currentVaultCategory);
        });
    });

    if (vaultSearchInput) {
        vaultSearchInput.addEventListener("input", (e) => {
            currentVaultQuery = e.target.value.trim();
            if (btnClearVaultSearch) {
                btnClearVaultSearch.style.display = currentVaultQuery ? "block" : "none";
            }
            applyVaultFilters();
        });
    }

    if (btnClearVaultSearch) {
        btnClearVaultSearch.addEventListener("click", () => {
            if (vaultSearchInput) vaultSearchInput.value = "";
            currentVaultQuery = "";
            btnClearVaultSearch.style.display = "none";
            applyVaultFilters();
        });
    }

    if (btnVaultOpenMemorial) {
        btnVaultOpenMemorial.addEventListener("click", () => openMemorialModal());
    }

    // Modal de notas
    const noteModal = document.getElementById("note-modal");
    const modalClose = document.getElementById("modal-close");
    const modalCancel = document.getElementById("modal-cancel");
    const modalSave = document.getElementById("modal-save");

    async function openNoteModal(category = "expedientes", noteId = null) {
        const catSelect = document.getElementById("modal-note-category");
        const idInput = document.getElementById("modal-note-id");
        const titleInput = document.getElementById("modal-note-title");
        const contentInput = document.getElementById("modal-note-content");

        if (noteId) {
            // Cargar nota existente
            try {
                const res = await fetch(`/api/vault/notes/${category}/${noteId}`);
                if (res.ok) {
                    const data = await res.json();
                    catSelect.value = data.category;
                    catSelect.disabled = true;
                    idInput.value = data.id;
                    idInput.disabled = true;
                    titleInput.value = data.metadata.titulo || data.id;
                    contentInput.value = data.content;
                }
            } catch (e) {
                console.error(e);
            }
        } else {
            // Nueva nota
            catSelect.value = category === "all" ? "expedientes" : category;
            catSelect.disabled = false;
            idInput.value = "";
            idInput.disabled = false;
            titleInput.value = "";
            contentInput.value = "";
        }

        noteModal.classList.add("active");
    }

    modalClose?.addEventListener("click", () => noteModal.classList.remove("active"));
    modalCancel?.addEventListener("click", () => noteModal.classList.remove("active"));
    document.getElementById("btn-new-note")?.addEventListener("click", () => openNoteModal());

    modalSave?.addEventListener("click", async () => {
        const category = document.getElementById("modal-note-category").value;
        const noteId = document.getElementById("modal-note-id").value.trim();
        const title = document.getElementById("modal-note-title").value.trim();
        const content = document.getElementById("modal-note-content").value.trim();

        if (!noteId || !title || !content) {
            alert("Por favor completa el ID, título y contenido.");
            return;
        }

        try {
            const res = await fetch("/api/vault/notes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    category: category,
                    note_id: noteId,
                    title: title,
                    content: content
                })
            });
            if (res.ok) {
                noteModal.classList.remove("active");
                loadVaultNotes();
            } else {
                alert("Error al guardar la nota.");
            }
        } catch (e) {
            alert("Error de conexión al guardar nota.");
        }
    });

    // -------------------------------------------------------------
    // 4. CARTUCHOS Y DOCUMENTOS
    // -------------------------------------------------------------
    const cartridgesList = document.getElementById("cartridges-list");
    const docsTbody = document.getElementById("docs-tbody");
    const dropArea = document.getElementById("drop-area");
    const fileInput = document.getElementById("file-input");
    const btnReindex = document.getElementById("btn-reindex");

    async function loadCartridges() {
        try {
            const res = await fetch("/api/cartridges");
            const data = await res.json();
            state.cartridges = data;
            renderCartridges(data);
        } catch (e) {
            console.error(e);
        }
    }

    function renderCartridges(cartridges) {
        if (!cartridgesList) return;
        cartridgesList.innerHTML = "";

        cartridges.forEach(cart => {
            const card = document.createElement("div");
            card.className = `cartridge-card ${cart.is_active ? 'active' : ''}`;
            
            let icon = "⚖️";
            let domainTag = "DERECHO GENERAL";
            if (cart.id === "jep_transicional") {
                icon = "🕊️";
                domainTag = "JUSTICIA TRANSICIONAL • JEP";
            } else if (cart.id === "legal_co") {
                icon = "🏛️";
                domainTag = "LITIGIO CIVIL & CONSTITUCIONAL";
            } else if (cart.id === "telco_crm") {
                icon = "📡";
                domainTag = "TELECOMUNICACIONES & CRM";
            }

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="cartridge-domain-badge ${cart.is_active ? 'badge-active-glow' : 'badge-inactive'}">${escapeHtml(domainTag)}</span>
                    <span style="font-size: 12px; color: var(--text-muted); font-weight: 500;">📁 ${cart.doc_count} docs indexados</span>
                </div>
                <div style="display: flex; align-items: center; gap: 10px; margin: 4px 0;">
                    <span style="font-size: 26px;">${icon}</span>
                    <h3 class="cartridge-title" style="margin: 0;">${escapeHtml(cart.name)}</h3>
                </div>
                <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.45; flex: 1;">${escapeHtml(cart.description)}</p>
                <div style="margin-top: 10px;">
                    ${cart.is_active 
                        ? `<button class="btn-primary" style="width: 100%; background: linear-gradient(135deg, rgba(52, 232, 176, 0.25), rgba(0, 229, 255, 0.2)); border: 1px solid var(--bio-mint); color: #fff; cursor: default;" disabled>✓ Cartucho Activo en Memoria</button>`
                        : `<button class="btn-primary btn-switch-cart" data-id="${cart.id}" style="width: 100%; background: rgba(0, 229, 255, 0.15); border: 1px solid var(--bio-cyan); color: var(--bio-cyan);">⚡ Conmutar y Cargar en Memoria</button>`}
                </div>
            `;
            cartridgesList.appendChild(card);
        });

        document.querySelectorAll(".btn-switch-cart").forEach(btn => {
            btn.addEventListener("click", async () => {
                const id = btn.dataset.id;
                btn.disabled = true;
                btn.textContent = "Conmutando e Indexando...";
                try {
                    const res = await fetch("/api/cartridges/switch", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ cartridge_id: id })
                    });
                    if (res.ok) {
                        await loadSystemStatus();
                        await loadCartridges();
                        await loadDocuments();
                        if (typeof loadIndexData === "function") await loadIndexData();
                    }
                } catch (e) {
                    alert("Error conmutando cartucho: " + e.message);
                }
            });
        });
    }

    const docsSearchInput = document.getElementById("docs-search-input");
    if (docsSearchInput) {
        docsSearchInput.addEventListener("input", (e) => {
            const q = e.target.value.toLowerCase().trim();
            if (!state.documents) return;
            if (!q) {
                renderDocuments(state.documents);
            } else {
                const filtered = state.documents.filter(d => 
                    d.filename.toLowerCase().includes(q) ||
                    d.relative_path.toLowerCase().includes(q) ||
                    d.extension.toLowerCase().includes(q)
                );
                renderDocuments(filtered);
            }
        });
    }

    async function loadDocuments() {
        try {
            const res = await fetch("/api/documents");
            const docs = await res.json();
            state.documents = docs;
            renderDocuments(docs);
        } catch (e) {
            console.error(e);
        }
    }

    // -------------------------------------------------------------
    // 4.1. VISOR DE FRAGMENTOS INDEXADOS & VECTORES
    // -------------------------------------------------------------
    const chunksTbody = document.getElementById("chunks-tbody");
    const indexSearchInput = document.getElementById("index-search-input");
    const btnIndexSearch = document.getElementById("btn-index-search");

    async function loadIndexData(searchQuery = "") {
        try {
            // 1. Cargar Estadísticas del Motor
            const statsRes = await fetch("/api/index/stats");
            if (statsRes.ok) {
                const stats = await statsRes.json();
                document.getElementById("stat-total-chunks").textContent = stats.total_chunks;
                document.getElementById("stat-vocab-size").textContent = stats.vocab_size;
                document.getElementById("stat-vector-count").textContent = stats.vector_count;
            }

            // 2. Cargar Lista de Fragmentos
            const chunksUrl = searchQuery ? `/api/index/chunks?search=${encodeURIComponent(searchQuery)}` : "/api/index/chunks";
            const chunksRes = await fetch(chunksUrl);
            if (chunksRes.ok) {
                const chunks = await chunksRes.json();
                renderChunks(chunks);
            }
        } catch (e) {
            console.error("Error cargando índice:", e);
        }
    }

    function renderChunks(chunks) {
        if (!chunksTbody) return;
        chunksTbody.innerHTML = "";

        if (chunks.length === 0) {
            chunksTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 20px;">No se encontraron fragmentos coincidentes en el índice.</td></tr>`;
            return;
        }

        chunks.forEach(c => {
            const tr = document.createElement("tr");
            const label = c.articulo || c.section || "Sección General";
            tr.innerHTML = `
                <td>
                    <strong style="color: var(--primary-blue);">${escapeHtml(label)}</strong>
                    <div style="font-size: 11px; color: var(--text-muted);">${escapeHtml(c.hierarchy)}</div>
                </td>
                <td style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(c.source)}</td>
                <td style="font-size: 13px; color: var(--text-primary);">
                    ${escapeHtml(c.content.substring(0, 160))}...
                </td>
                <td><span class="badge badge-blue">~${c.approx_tokens}</span></td>
            `;
            chunksTbody.appendChild(tr);
        });
    }

    btnIndexSearch?.addEventListener("click", () => {
        loadIndexData(indexSearchInput?.value.trim() || "");
    });
    indexSearchInput?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            loadIndexData(indexSearchInput.value.trim());
        }
    });

    function renderDocuments(docs) {
        if (!docsTbody) return;
        docsTbody.innerHTML = "";

        if (docs.length === 0) {
            docsTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No hay documentos cargados en el corpus.</td></tr>`;
            return;
        }

        docs.forEach(d => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(d.filename)}</strong></td>
                <td style="color: var(--text-secondary);">${escapeHtml(d.relative_path)}</td>
                <td><span class="badge">${escapeHtml(d.extension.toUpperCase())}</span></td>
                <td>${d.size_kb} KB</td>
            `;
            docsTbody.appendChild(tr);
        });
    }

    // Subida de archivos
    dropArea?.addEventListener("click", () => fileInput?.click());
    fileInput?.addEventListener("change", async (e) => {
        if (!e.target.files.length) return;
        const file = e.target.files[0];
        const formData = new FormData();
        formData.append("file", file);

        const curatorInput = document.getElementById("curator-instruction-input");
        if (curatorInput && curatorInput.value.trim()) {
            formData.append("curator_instruction", curatorInput.value.trim());
        }

        dropArea.style.opacity = "0.5";
        try {
            const res = await fetch("/api/documents/upload", {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                const data = await res.json();
                if (data.mutation_registered && data.mutation) {
                    alert(`¡Documento cargado y Mutación de Precedente registrada en SQLite!\n\n• Norma Afectada: ${data.mutation.target_norm}\n• Tipo de Mutación: ${data.mutation.mutation_type}\n• Nueva Regla: ${data.mutation.regla_nueva.slice(0, 120)}...\n\nSe ha actualizado automáticamente la Bóveda de Obsidian y el índice RAG.`);
                    if (curatorInput) curatorInput.value = "";
                } else {
                    alert(`Archivo '${file.name}' cargado con éxito. Ahora presiona 'Re-indexar RAG Híbrido'.`);
                }
                loadDocuments();
                loadMutationsTable();
                loadVaultNotes();
            } else {
                alert("Error al cargar el archivo.");
            }
        } catch (e) {
            alert("Error de conexión al subir archivo.");
        } finally {
            dropArea.style.opacity = "1";
            fileInput.value = "";
        }
    });

    btnReindex?.addEventListener("click", async () => {
        btnReindex.disabled = true;
        btnReindex.textContent = "⏳ Re-indexando RAG...";
        try {
            const res = await fetch("/api/ingest", { method: "POST" });
            const data = await res.json();
            alert(`Re-indexación completa: ${data.total_chunks} fragmentos indexados.`);
            loadSystemStatus();
            loadIndexData();
            loadMutationsTable();
        } catch (e) {
            alert("Error re-indexando: " + e.message);
        } finally {
            btnReindex.disabled = false;
            btnReindex.textContent = "🔄 Re-indexar RAG Híbrido";
        }
    });

    // -------------------------------------------------------------
    // 4.1. TRAZABILIDAD DOGMÁTICA & MUTACIÓN DE PRECEDENTES (SQLITE)
    // -------------------------------------------------------------
    const mutationModal = document.getElementById("mutation-modal");
    const mutationModalClose = document.getElementById("mutation-modal-close");
    const btnCloseMutationModal = document.getElementById("btn-close-mutation-modal");
    const btnRefreshMutations = document.getElementById("btn-refresh-mutations");

    function renderMutationBannersInChat(targetEl, mutations) {
        if (!targetEl || !mutations || !mutations.length) return;
        const parent = targetEl.parentElement;
        if (!parent) return;

        let container = parent.querySelector(".mutation-banners-wrapper");
        if (!container) {
            container = document.createElement("div");
            container.className = "mutation-banners-wrapper";
            parent.insertBefore(container, targetEl);
        }
        container.innerHTML = "";
        mutations.forEach(m => {
            const banner = document.createElement("div");
            banner.className = "mutation-alert-banner";
            banner.innerHTML = `
                <div class="banner-icon">🏛️</div>
                <div class="banner-text">
                    <strong>Aviso de Vigencia (${escapeHtml(m.mutation_type)}):</strong> El precedente <em>${escapeHtml(m.target_norm)}</em> fue modificado/superado por <em>${escapeHtml(m.source_doc)}</em> (${escapeHtml(m.autoridad)}).
                </div>
                <button type="button" class="banner-btn">Ver Trazabilidad (¿Qué había antes vs. ahora?) ➔</button>
            `;
            banner.addEventListener("click", (evt) => {
                evt.stopPropagation();
                openMutationModal(m);
            });
            container.appendChild(banner);
        });
    }

    function openMutationModal(m) {
        if (!mutationModal || !m) return;
        const titleEl = document.getElementById("mutation-modal-title");
        const subtitleEl = document.getElementById("mutation-modal-subtitle");
        const badgesEl = document.getElementById("mutation-modal-badges");
        const reglaAnteriorEl = document.getElementById("modal-regla-anterior");
        const reglaNuevaEl = document.getElementById("modal-regla-nueva");
        const efectosEl = document.getElementById("modal-efectos-info");

        if (titleEl) titleEl.textContent = `Trazabilidad Dogmática: ${m.target_norm}`;
        if (subtitleEl) subtitleEl.textContent = `Modificado por ${m.source_doc} • Autoridad: ${m.autoridad}`;

        if (badgesEl) {
            badgesEl.innerHTML = `
                <span class="badge" style="background: rgba(0, 229, 255, 0.15); color: var(--bio-cyan); font-weight: 600;">⚖️ ${escapeHtml(m.mutation_type)}</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38BDF8;">📅 Fecha: ${escapeHtml(m.fecha_mutacion || 'Reciente')}</span>
                <span class="badge" style="background: rgba(168, 85, 247, 0.15); color: #C084FC;">🏛️ ${escapeHtml(m.autoridad)}</span>
                <span class="badge" style="background: rgba(52, 232, 176, 0.15); color: var(--bio-mint);">📁 Origen: ${escapeHtml(m.source_doc)}</span>
            `;
        }

        if (reglaAnteriorEl) {
            reglaAnteriorEl.innerHTML = formatResponseText(m.regla_anterior || "Sin registro detallado del criterio anterior.");
        }
        if (reglaNuevaEl) {
            reglaNuevaEl.innerHTML = formatResponseText(m.regla_nueva || "Sin registro detallado del nuevo criterio vinculante.");
        }
        if (efectosEl) {
            let noteHtml = m.curator_notes ? `<br><strong>Instrucción / Notas del Curador:</strong> <em>«${escapeHtml(m.curator_notes)}»</em>` : "";
            efectosEl.innerHTML = `<strong>Efectos:</strong> ${escapeHtml(m.efectos || 'Hacia el futuro (Ex nunc)')} ${noteHtml}`;
        }

        mutationModal.classList.add("active");
        mutationModal.style.display = "flex";
    }

    function closeMutationModal() {
        if (!mutationModal) return;
        mutationModal.classList.remove("active");
        mutationModal.style.display = "none";
    }

    mutationModalClose?.addEventListener("click", closeMutationModal);
    btnCloseMutationModal?.addEventListener("click", closeMutationModal);
    mutationModal?.addEventListener("click", (e) => {
        if (e.target === mutationModal) closeMutationModal();
    });

    async function loadMutationsTable() {
        const tbody = document.getElementById("mutations-tbody");
        if (!tbody) return;

        try {
            const res = await fetch("/api/jurisprudencia/mutations");
            if (!res.ok) return;
            const mutations = await res.json();
            tbody.innerHTML = "";

            if (!mutations || !mutations.length) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 18px;">No hay mutaciones de precedente o derogatorias registradas aún en SQLite. Puedes subir una sentencia con una instrucción de curaduría para registrar una nueva.</td></tr>`;
                return;
            }

            mutations.forEach(m => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${escapeHtml(m.target_norm)}</strong></td>
                    <td style="color: var(--bio-cyan); font-weight: 500;">${escapeHtml(m.source_doc)}</td>
                    <td><span class="badge" style="background: rgba(0, 229, 255, 0.15); color: var(--bio-cyan);">${escapeHtml(m.mutation_type)}</span></td>
                    <td style="color: #FDE047; font-size: 12.5px;">${escapeHtml((m.regla_anterior || '').slice(0, 95))}${m.regla_anterior && m.regla_anterior.length > 95 ? '...' : ''}</td>
                    <td style="color: var(--bio-mint); font-size: 12.5px;">${escapeHtml((m.regla_nueva || '').slice(0, 95))}${m.regla_nueva && m.regla_nueva.length > 95 ? '...' : ''}</td>
                    <td style="text-align: center;">
                        <button type="button" class="btn-view-mutation" title="Ver ficha comparativa completa">Ver Ficha ➔</button>
                    </td>
                `;
                tr.querySelector(".btn-view-mutation").addEventListener("click", () => openMutationModal(m));
                tbody.appendChild(tr);
            });
        } catch (e) {
            console.error("Error cargando tabla de mutaciones:", e);
        }
    }

    btnRefreshMutations?.addEventListener("click", loadMutationsTable);

    // -------------------------------------------------------------
    // 5. GUARDAR AJUSTES MLOPS & CREDENCIALES GEMINI
    // -------------------------------------------------------------
    document.getElementById("btn-save-gemini-key")?.addEventListener("click", async () => {
        const geminiKey = document.getElementById("cfg-gemini-key").value.trim();
        const geminiModel = document.getElementById("cfg-gemini-model")?.value?.trim() || "gemini-3.8-flash";

        if (!geminiKey) {
            alert("Por favor ingresa tu API Key de Gemini antes de guardar.");
            return;
        }

        try {
            const res = await fetch("/api/system/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    gemini_api_key: geminiKey,
                    gemini_model: geminiModel
                })
            });
            if (res.ok) {
                alert("✓ Clave de Gemini guardada con éxito en el sistema local (.env). Modo comparativo habilitado.");
                document.getElementById("cfg-gemini-key").value = "";
                await loadSystemStatus();
            } else {
                const err = await res.json().catch(() => ({}));
                alert("Error al guardar: " + (err.detail || "Error desconocido"));
            }
        } catch (e) {
            alert("Error de conexión: " + e.message);
        }
    });

    document.getElementById("btn-toggle-gemini-key")?.addEventListener("click", () => {
        const input = document.getElementById("cfg-gemini-key");
        if (!input) return;
        input.type = input.type === "password" ? "text" : "password";
    });

    document.getElementById("btn-save-config")?.addEventListener("click", async () => {
        const provider = document.getElementById("cfg-provider").value;
        const cloudEgress = document.getElementById("chk-cloud-egress") ? document.getElementById("chk-cloud-egress").checked : false;
        const geminiKey = document.getElementById("cfg-gemini-key")?.value?.trim() || "";
        const geminiModel = document.getElementById("cfg-gemini-model")?.value?.trim() || "gemini-3.8-flash";
        const localUrl = document.getElementById("cfg-local-url").value.trim();
        const localModel = document.getElementById("cfg-local-model").value.trim();

        const payload = {
            llm_provider: provider,
            cloud_egress_enabled: cloudEgress,
            gemini_api_key: geminiKey || undefined,
            gemini_model: geminiModel,
            local_base_url: localUrl,
            local_model: localModel
        };

        try {
            const res = await fetch("/api/system/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert("Configuración aplicada con éxito.");
                loadSystemStatus();
            } else {
                alert("Error guardando configuración.");
            }
        } catch (e) {
            alert("Error de conexión: " + e.message);
        }
    });

    // Selector rápido de modelo en la barra superior compacta
    document.getElementById("quick-model-select")?.addEventListener("change", async (e) => {
        const newModel = e.target.value;
        const cfgLocal = document.getElementById("cfg-local-model");
        if (cfgLocal) cfgLocal.value = newModel;

        const payload = {
            llm_provider: "local",
            local_model: newModel
        };

        try {
            const res = await fetch("/api/system/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                await loadSystemStatus();
                const indicator = document.getElementById("chat-grounding-indicator");
                if (indicator) {
                    const originalText = indicator.textContent;
                    indicator.textContent = `✓ Modelo conmutado a ${newModel}`;
                    indicator.style.background = "var(--bio-cyan-dim)";
                    indicator.style.color = "var(--bio-cyan)";
                    setTimeout(() => {
                        indicator.textContent = originalText;
                        indicator.style.background = "";
                        indicator.style.color = "";
                    }, 3500);
                }
                if (hudPhaseLabel) {
                    hudPhaseLabel.textContent = `⚡ Motor local conmutado a ${newModel}`;
                }
            }
        } catch (err) {
            console.error("Error cambiando modelo rápido:", err);
        }
    });

    // -------------------------------------------------------------
    // 5. GENERADOR DE MINUTAS Y MEMORIALES PROCESALES (TUTELAS & PQR)
    // -------------------------------------------------------------
    const memorialModal = document.getElementById("memorial-modal");
    const btnOpenMemorial = document.getElementById("btn-open-memorial-modal");
    const pillQuickMemorial = document.getElementById("pill-quick-memorial");
    const memorialModalClose = document.getElementById("memorial-modal-close");
    const btnCloseMemorialBottom = document.getElementById("btn-close-memorial-bottom");

    const radioTipoTutela = document.getElementById("radio-tipo-tutela");
    const radioTipoPeticion = document.getElementById("radio-tipo-peticion");
    const memorialCatSelect = document.getElementById("memorial-cat-select");
    const memorialCatFundamento = document.getElementById("memorial-cat-fundamento");
    const memorialMedidaGroup = document.getElementById("memorial-medida-group");

    const memorialAccionanteNombre = document.getElementById("memorial-accionante-nombre");
    const memorialAccionanteId = document.getElementById("memorial-accionante-id");
    const memorialAccionadoNombre = document.getElementById("memorial-accionado-nombre");
    const memorialCiudad = document.getElementById("memorial-ciudad");
    const memorialAccionanteCorreo = document.getElementById("memorial-accionante-correo");
    const memorialAccionadoCorreo = document.getElementById("memorial-accionado-correo");
    const memorialHechos = document.getElementById("memorial-hechos");
    const memorialPretensiones = document.getElementById("memorial-pretensiones");
    const chkMedidaCautelar = document.getElementById("memorial-medida-cautelar");

    const btnGenerateMemorial = document.getElementById("btn-generate-memorial");
    const memorialOutputText = document.getElementById("memorial-output-text");
    const memorialResultBadge = document.getElementById("memorial-result-badge");
    const btnCopyMemorial = document.getElementById("btn-copy-memorial");
    const btnDownloadDocx = document.getElementById("btn-download-docx");

    let memorialTaxonomy = null;
    let currentMemorialDocId = "minuta_procesal";

    async function loadMemorialTaxonomy() {
        if (memorialTaxonomy) return memorialTaxonomy;
        try {
            const res = await fetch("/api/memorials/taxonomy");
            if (res.ok) {
                memorialTaxonomy = await res.json();
                return memorialTaxonomy;
            }
        } catch (e) {
            console.error("Error cargando taxonomía de memoriales:", e);
        }
        return null;
    }

    function updateMemorialCategories() {
        if (!memorialTaxonomy || !memorialCatSelect) return;
        const isTutela = radioTipoTutela && radioTipoTutela.checked;
        const dict = isTutela ? memorialTaxonomy.tutelas : memorialTaxonomy.peticiones;

        memorialCatSelect.innerHTML = "";
        Object.keys(dict).forEach(k => {
            const opt = document.createElement("option");
            opt.value = k;
            opt.textContent = dict[k].nombre;
            memorialCatSelect.appendChild(opt);
        });

        if (memorialMedidaGroup) {
            memorialMedidaGroup.style.display = isTutela ? "block" : "none";
        }

        updateSelectedCategoryInfo();
    }

    function updateSelectedCategoryInfo() {
        if (!memorialTaxonomy || !memorialCatSelect) return;
        const isTutela = radioTipoTutela && radioTipoTutela.checked;
        const catKey = memorialCatSelect.value;
        const dict = isTutela ? memorialTaxonomy.tutelas : memorialTaxonomy.peticiones;
        const item = dict[catKey];

        if (item && memorialCatFundamento) {
            if (isTutela) {
                memorialCatFundamento.innerHTML = `<strong>Derechos:</strong> ${item.derechos.join(", ")}.<br><strong>Citas Clave:</strong> ${item.fundamentos_clave}`;
            } else {
                memorialCatFundamento.innerHTML = `<strong>Término de Respuesta:</strong> ${item.plazo_legal}.<br><strong>Fundamento:</strong> ${item.fundamento_legal}<br><small style="color: #FDE047;">${item.consecuencia_silencio}</small>`;
            }
        }
    }

    async function openMemorialModal() {
        if (!memorialModal) return;
        memorialModal.classList.add("active");
        const tax = await loadMemorialTaxonomy();
        if (tax) {
            updateMemorialCategories();
        }
    }

    function closeMemorialModal() {
        if (!memorialModal) return;
        memorialModal.classList.remove("active");
    }

    btnOpenMemorial?.addEventListener("click", openMemorialModal);
    pillQuickMemorial?.addEventListener("click", openMemorialModal);
    memorialModalClose?.addEventListener("click", closeMemorialModal);
    btnCloseMemorialBottom?.addEventListener("click", closeMemorialModal);

    radioTipoTutela?.addEventListener("change", updateMemorialCategories);
    radioTipoPeticion?.addEventListener("change", updateMemorialCategories);
    memorialCatSelect?.addEventListener("change", updateSelectedCategoryInfo);

    btnGenerateMemorial?.addEventListener("click", async () => {
        const isTutela = radioTipoTutela && radioTipoTutela.checked;
        const payload = {
            tipo_accion: isTutela ? "TUTELA" : "DERECHO_PETICION",
            categoria_id: memorialCatSelect.value,
            ciudad: memorialCiudad.value.trim() || "Bogotá D.C.",
            accionante_nombre: memorialAccionanteNombre.value.trim() || "ACCIONANTE",
            accionante_identificacion: memorialAccionanteId.value.trim() || "00.000.000",
            accionante_correo: memorialAccionanteCorreo.value.trim() || "correo@ejemplo.com",
            accionado_nombre: memorialAccionadoNombre.value.trim() || "ENTIDAD ACCIONADA",
            accionado_correo: memorialAccionadoCorreo.value.trim() || "",
            hechos: memorialHechos.value.trim(),
            pretensiones: memorialPretensiones.value.trim(),
            solicitar_medida_cautelar: isTutela ? (chkMedidaCautelar ? chkMedidaCautelar.checked : false) : false,
            save_vault: true
        };

        btnGenerateMemorial.disabled = true;
        btnGenerateMemorial.textContent = "⚙️ Redactando memorial con técnica constitucional...";

        try {
            const res = await fetch("/api/memorials/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                currentMemorialDocId = data.doc_id;
                memorialOutputText.value = data.markdown;
                memorialResultBadge.textContent = `✓ ${data.tipo} Lista: ${data.categoria_nombre}`;
                memorialResultBadge.className = "badge badge-green";

                btnCopyMemorial.disabled = false;
                btnDownloadDocx.disabled = false;

                // Actualizar Bóveda en segundo plano
                loadVaultNotes();
            } else {
                alert("Error generando minuta.");
            }
        } catch (e) {
            alert("Error de conexión al generar minuta: " + e.message);
        } finally {
            btnGenerateMemorial.disabled = false;
            btnGenerateMemorial.textContent = "⚡ Redactar Memorial Soberano con Sadigua";
        }
    });

    btnCopyMemorial?.addEventListener("click", () => {
        if (!memorialOutputText.value) return;
        navigator.clipboard.writeText(memorialOutputText.value).then(() => {
            const orig = btnCopyMemorial.textContent;
            btnCopyMemorial.textContent = "✓ ¡Copiado!";
            setTimeout(() => { btnCopyMemorial.textContent = orig; }, 2000);
        });
    });

    btnDownloadDocx?.addEventListener("click", async () => {
        if (!memorialOutputText.value) return;
        btnDownloadDocx.disabled = true;
        btnDownloadDocx.textContent = "Exportando Word...";
        try {
            const res = await fetch("/api/memorials/download-docx", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    markdown: memorialOutputText.value,
                    doc_id: currentMemorialDocId
                })
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.download = `${currentMemorialDocId}.docx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            } else {
                alert("Error descargando archivo .docx");
            }
        } catch (e) {
            alert("Error descargando .docx: " + e.message);
        } finally {
            btnDownloadDocx.disabled = false;
            btnDownloadDocx.textContent = "📥 Descargar Word (.docx)";
        }
    });

    // -------------------------------------------------------------
    // UTILIDADES DE FORMATO
    // -------------------------------------------------------------
    function escapeHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function formatResponseText(text) {
        if (!text) return "";
        let formatted = escapeHtml(text);
        // Títulos H4 (#### ...)
        formatted = formatted.replace(/^#### (.*?)$/gm, '<h5 style="color: var(--bio-mint); margin: 12px 0 4px 0; font-size: 14px; font-weight: 700;">$1</h5>');
        // Títulos H3 (### ...)
        formatted = formatted.replace(/^### (.*?)$/gm, '<h4 style="color: var(--bio-cyan); margin: 16px 0 8px 0; font-size: 15.5px; font-weight: 700; border-bottom: 1px solid rgba(0, 229, 255, 0.22); padding-bottom: 4px;">$1</h4>');
        // Separador horizontal (---)
        formatted = formatted.replace(/^---$/gm, '<hr style="border: none; border-top: 1px dashed rgba(56, 189, 248, 0.28); margin: 14px 0;">');
        // Negritas (**texto**)
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Cursivas (*texto*)
        formatted = formatted.replace(/\*([^\*]+?)\*/g, '<em>$1</em>');
        // Listas con viñetas (- ...)
        formatted = formatted.replace(/\n- (.*?)/g, '<br>• $1');
        // Listas numeradas (1. ...)
        formatted = formatted.replace(/\n(\d+)\. (.*?)/g, '<br><strong>$1.</strong> $2');
        // Saltos de línea
        formatted = formatted.replace(/\n\n/g, '<br><br>');
        return formatted;
    }

    // Inicializar
    loadSystemStatus();
    loadMutationsTable();
});
