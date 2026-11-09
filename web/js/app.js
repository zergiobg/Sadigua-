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
        isQuerying: false
    };

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

            // Recargar datos específicos según la pestaña seleccionada
            if (targetTab === "tab-vault") loadVaultNotes();
            if (targetTab === "tab-cartridges") {
                loadCartridges();
                loadDocuments();
                loadIndexData();
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

            // Actualizar badges del encabezado
            document.getElementById("header-provider").textContent = 
                data.provider === "gemini" ? `Gemini (${data.gemini_model})` : `Local (${data.local_model})`;
            document.getElementById("header-cartridge").textContent = data.active_cartridge;

            // Actualizar Compuerta de Soberanía
            updateSovereigntyUI(data.cloud_egress_enabled);

            // Configurar formulario de ajustes
            const providerSelect = document.getElementById("cfg-provider");
            if (providerSelect) {
                providerSelect.value = data.provider;
                toggleProviderFields(data.provider);
            }
            if (data.gemini_model) document.getElementById("cfg-gemini-model").value = data.gemini_model;
            if (data.local_url) document.getElementById("cfg-local-url").value = data.local_url;
            if (data.local_model) {
                const cfgLocal = document.getElementById("cfg-local-model");
                if (cfgLocal) cfgLocal.value = data.local_model;
                const quickSelect = document.getElementById("quick-model-select");
                if (quickSelect) quickSelect.value = data.local_model;
            }

        } catch (e) {
            console.error("No se pudo conectar al backend de Sadigua:", e);
        }
    }

    function updateSovereigntyUI(egressEnabled) {
        const badgeSov = document.getElementById("badge-sovereignty");
        const pillSov = document.getElementById("egress-status-pill");
        const chkEgress = document.getElementById("chk-cloud-egress");

        if (chkEgress) chkEgress.checked = Boolean(egressEnabled);

        if (egressEnabled) {
            if (badgeSov) {
                badgeSov.className = "badge badge-blue";
                badgeSov.innerHTML = "<span>🌐</span> <strong>Modo Híbrido (Nube Autorizada)</strong>";
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
            if (pillSov) {
                pillSov.className = "badge badge-green";
                pillSov.textContent = "🔒 Salida a Nube Bloqueada";
            }
        }
    }

    function toggleProviderFields(provider) {
        const geminiFields = document.getElementById("cfg-gemini-fields");
        const localFields = document.getElementById("cfg-local-fields");
        if (provider === "gemini") {
            geminiFields.style.display = "block";
            localFields.style.display = "none";
        } else {
            geminiFields.style.display = "none";
            localFields.style.display = "block";
        }
    }

    document.getElementById("cfg-provider")?.addEventListener("change", (e) => {
        toggleProviderFields(e.target.value);
    });

    // -------------------------------------------------------------
    // 2. CHAT JURÍDICO INTERACTIVO & TELEMETRÍA EN VIVO (ONDAS)
    // -------------------------------------------------------------
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const btnSend = document.getElementById("btn-send");
    const chkAnonymize = document.getElementById("chk-anonymize");

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

    function resetHUD() {
        if (!chatHud) return;
        chatHud.classList.remove("hidden");
        if (hudPhaseLabel) hudPhaseLabel.textContent = "Iniciando consulta jurídica...";
        if (hudProgressFill) hudProgressFill.style.width = "5%";
        if (hudBadgeCache) hudBadgeCache.classList.add("hidden");
        if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill active";
        if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill pending";
        if (hudDocsList) hudDocsList.innerHTML = "";
    }

    async function sendQuery(queryText) {
        if (!queryText || state.isQuerying) return;
        state.isQuerying = true;
        btnSend.disabled = true;

        appendUserMessage(queryText);
        chatInput.value = "";

        resetHUD();
        startStopwatch();

        // Crear contenedor para mensaje progresivo del asistente
        const currentMsgId = "msg-" + Date.now();
        const wrapper = document.createElement("div");
        wrapper.className = "msg-wrapper assistant";
        wrapper.id = currentMsgId;
        wrapper.innerHTML = `
            <div class="msg-avatar assistant">S</div>
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

        const contentEl = document.getElementById(`${currentMsgId}-content`);
        const badgesEl = document.getElementById(`${currentMsgId}-badges`);
        const sourcesEl = document.getElementById(`${currentMsgId}-sources`);

        let accumulatedText = "";
        let isWave2Started = false;

        try {
            const res = await fetch("/api/chat/progressive", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: queryText,
                    anonymize: chkAnonymize ? chkAnonymize.checked : true
                })
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
                            if (event.phase === "wave_1_start") {
                                if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill active";
                            } else if (event.phase === "wave_1_continuation") {
                                if (hudPhaseLabel) hudPhaseLabel.textContent = "🛡️ Completando cierre de idea en Onda 1...";
                            } else if (event.phase === "wave_1_done") {
                                if (hudBadgeWave1) hudBadgeWave1.className = "wave-pill done";
                                if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill active";
                                // Píldora de espera activa para informar al usuario que se está cocinando la Onda 2
                                if (contentEl && !document.getElementById("wave2-cooking-pill")) {
                                    const pill = document.createElement("div");
                                    pill.id = "wave2-cooking-pill";
                                    pill.className = "wave2-cooking-pill";
                                    pill.innerHTML = `<span class="hud-spinner"></span> <span><strong>Cocinando Onda 2:</strong> Redactando Ruta Procesal, Tutela y Acciones Concretas...</span>`;
                                    contentEl.parentElement.appendChild(pill);
                                    chatMessages.scrollTop = chatMessages.scrollHeight;
                                }
                            } else if (event.phase === "wave_2_start") {
                                if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill active";
                            } else if (event.phase === "wave_2_continuation") {
                                if (hudPhaseLabel) hudPhaseLabel.textContent = "🛡️ Completando recomendaciones y cierre final...";
                            } else if (event.phase === "wave_2_done") {
                                if (hudBadgeWave2) hudBadgeWave2.className = "wave-pill done";
                                const cookingPill = document.getElementById("wave2-cooking-pill");
                                if (cookingPill) cookingPill.remove();
                            }
                        } else if (event.type === "documents_found") {
                            if (hudDocsList && event.documents) {
                                hudDocsList.innerHTML = event.documents.map(d => {
                                    const lbl = d.articulo || d.section || "Norma";
                                    return `<span class="doc-pill" title="${escapeHtml(d.source)}">📄 ${escapeHtml(lbl)}</span>`;
                                }).join("");
                            }
                            if (hudProgressFill && event.progress) {
                                hudProgressFill.style.width = `${event.progress}%`;
                            }
                        } else if (event.type === "token") {
                            if (event.wave === 2 && !isWave2Started) {
                                isWave2Started = true;
                                const cookingPill = document.getElementById("wave2-cooking-pill");
                                if (cookingPill) cookingPill.remove();
                                accumulatedText += "\n\n---\n\n### Ruta Procesal, Tutela y Acciones Concretas\n\n";
                            }
                            accumulatedText += event.text;
                            if (contentEl) {
                                contentEl.innerHTML = formatResponseText(accumulatedText) + '<span class="streaming-cursor"></span>';
                            }
                            chatMessages.scrollTop = chatMessages.scrollHeight;
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
                            if (contentEl) {
                                contentEl.innerHTML = formatResponseText(accumulatedText);
                            }
                            renderSources(sourcesEl, event.sources);
                        } else if (event.type === "grounding") {
                            if (badgesEl) {
                                badgesEl.innerHTML = event.grounded
                                    ? `<span class="badge badge-green">✓ Grounding Verificado en Corpus</span>`
                                    : `<span class="badge" style="background: var(--warning-bg); color: var(--warning-text);">⚠️ ${escapeHtml(event.grounding_status)}</span>`;
                            }
                            renderSources(sourcesEl, event.sources);
                        } else if (event.type === "done") {
                            const cookingPill = document.getElementById("wave2-cooking-pill");
                            if (cookingPill) cookingPill.remove();
                            const totalDuration = stopStopwatch();
                            if (hudProgressFill) hudProgressFill.style.width = "100%";
                            if (hudPhaseLabel) hudPhaseLabel.textContent = `✓ Respuesta completada y archivada en Bóveda (${totalDuration}s)`;
                            if (contentEl) {
                                contentEl.innerHTML = formatResponseText(accumulatedText);
                            }
                        } else if (event.type === "error") {
                            throw new Error(event.message);
                        }
                    } catch (parseErr) {
                        console.warn("Línea SSE:", jsonStr, parseErr);
                    }
                }
            }
        } catch (e) {
            stopStopwatch();
            if (hudPhaseLabel) hudPhaseLabel.textContent = `❌ Error: ${e.message}`;
            appendErrorMessage(e.message);
        } finally {
            state.isQuerying = false;
            btnSend.disabled = false;
            chatInput.focus();
        }
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
            <div class="msg-bubble" style="border-color: #FCA5A5; background: var(--danger-bg); color: var(--danger-text);">
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
    const filterBtns = document.querySelectorAll(".filter-btn");

    async function loadVaultNotes(category = "all") {
        try {
            const url = category === "all" ? "/api/vault/notes" : `/api/vault/notes?category=${category}`;
            const res = await fetch(url);
            const notes = await res.json();
            state.notes = notes;
            renderVaultNotes(notes);
        } catch (e) {
            console.error("Error cargando notas de la bóveda:", e);
        }
    }

    function renderVaultNotes(notes) {
        if (!vaultGrid) return;
        vaultGrid.innerHTML = "";

        if (notes.length === 0) {
            vaultGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-secondary);">
                    <p style="font-size: 32px; margin-bottom: 8px;">📂</p>
                    <p style="font-weight: 600;">No hay notas registradas en esta categoría.</p>
                    <p style="font-size: 13px;">Haz clic en '+ Nueva Ficha' para registrar un expediente o cliente.</p>
                </div>
            `;
            return;
        }

        notes.forEach(note => {
            const card = document.createElement("div");
            card.className = "note-card";
            card.innerHTML = `
                <div class="note-header">
                    <span class="note-category">${escapeHtml(note.category)}</span>
                    <span style="font-size: 11px; color: var(--text-muted);">${escapeHtml(note.id)}</span>
                </div>
                <h4 class="note-title">${escapeHtml(note.title)}</h4>
                <p class="note-snippet">${escapeHtml(note.snippet)}</p>
                <div class="note-footer">
                    <span>📅 ${escapeHtml(note.updated || 'Reciente')}</span>
                    <span style="color: var(--primary-blue); font-weight: 500;">Ver Ficha ➔</span>
                </div>
            `;
            card.addEventListener("click", () => openNoteModal(note.category, note.id));
            vaultGrid.appendChild(card);
        });
    }

    filterBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            filterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadVaultNotes(btn.dataset.cat);
        });
    });

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
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge ${cart.is_active ? 'badge-blue' : ''}">${cart.is_active ? 'Activo' : 'Disponible'}</span>
                    <span style="font-size: 12px; color: var(--text-muted);">${cart.doc_count} documentos</span>
                </div>
                <h3 class="cartridge-title">${escapeHtml(cart.name)}</h3>
                <p style="font-size: 13px; color: var(--text-secondary); flex: 1;">${escapeHtml(cart.description)}</p>
                <div>
                    ${cart.is_active 
                        ? `<button class="btn-primary" style="width: 100%; opacity: 0.8;" disabled>✓ En Ejecución</button>`
                        : `<button class="btn-primary btn-switch-cart" data-id="${cart.id}" style="width: 100%;">Activar Cartucho</button>`}
                </div>
            `;
            cartridgesList.appendChild(card);
        });

        document.querySelectorAll(".btn-switch-cart").forEach(btn => {
            btn.addEventListener("click", async () => {
                const id = btn.dataset.id;
                btn.disabled = true;
                btn.textContent = "Conmutando...";
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
                    }
                } catch (e) {
                    alert("Error conmutando cartucho: " + e.message);
                }
            });
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

        dropArea.style.opacity = "0.5";
        try {
            const res = await fetch("/api/documents/upload", {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                alert(`Archivo '${file.name}' cargado con éxito. Ahora presiona 'Re-indexar RAG Híbrido'.`);
                loadDocuments();
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
        } catch (e) {
            alert("Error re-indexando: " + e.message);
        } finally {
            btnReindex.disabled = false;
            btnReindex.textContent = "🔄 Re-indexar RAG Híbrido";
        }
    });

    // -------------------------------------------------------------
    // 5. GUARDAR AJUSTES MLOPS
    // -------------------------------------------------------------
    document.getElementById("btn-save-config")?.addEventListener("click", async () => {
        const provider = document.getElementById("cfg-provider").value;
        const cloudEgress = document.getElementById("chk-cloud-egress") ? document.getElementById("chk-cloud-egress").checked : false;
        const geminiKey = document.getElementById("cfg-gemini-key").value.trim();
        const geminiModel = document.getElementById("cfg-gemini-model").value.trim();
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

    // Selector rápido de modelo en la barra del chat
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
                    indicator.style.background = "#DBEAFE";
                    indicator.style.color = "#1D4ED8";
                    setTimeout(() => {
                        indicator.textContent = originalText;
                        indicator.style.background = "";
                        indicator.style.color = "";
                    }, 3500);
                }
            }
        } catch (err) {
            console.error("Error cambiando modelo rápido:", err);
        }
    });

    // -------------------------------------------------------------
    // UTILIDADES DE FORMATO
    // -------------------------------------------------------------
    function escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatResponseText(text) {
        if (!text) return "";
        let formatted = escapeHtml(text);
        // Títulos H4 (#### ...)
        formatted = formatted.replace(/^#### (.*?)$/gm, '<h5 style="color: var(--primary-blue); margin: 12px 0 4px 0; font-size: 14px; font-weight: 700;">$1</h5>');
        // Títulos H3 (### ...)
        formatted = formatted.replace(/^### (.*?)$/gm, '<h4 style="color: var(--primary-blue); margin: 16px 0 8px 0; font-size: 15.5px; font-weight: 700; border-bottom: 1px solid #DBEAFE; padding-bottom: 4px;">$1</h4>');
        // Separador horizontal (---)
        formatted = formatted.replace(/^---$/gm, '<hr style="border: none; border-top: 1px dashed #CBD5E1; margin: 14px 0;">');
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
});
