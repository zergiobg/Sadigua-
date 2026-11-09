/**
 * SADIGUA NEURAL VISUALIZER v3 — Motor Anatómico Secuencial, Flares Neuronales,
 * Pipeline Sináptico Estático con Flare de Datos y Destello Final en los Ojos del Tótem (60 FPS).
 */
(function () {
    "use strict";

    const COGNITIVE_LAYERS = {
        1: {
            id: 1,
            shortLabel: "1/7 • PII & Tokens",
            badge: "ETAPA 1/7 • ESCUDO PII & TOKENIZACIÓN",
            region: "Collar Pectoral Geométrico Muisca",
            title: "1º Anonimización Soberana (Ley 1581) y Tokenización",
            desc: "Primero ingresa tu consulta por los filamentos pectorales: se enmascaran datos sensibles y el texto se divide en tokens y conceptos jurídicos clave.",
            color: "#00E5FF",
            svgOrigin: { x: 391, y: 615 }
        },
        2: {
            id: 2,
            shortLabel: "2/7 • Memoria Obsidian",
            badge: "ETAPA 2/7 • MEMORIA EPISÓDICA OBSIDIANA",
            region: "Espirales Oculares del Tótem",
            title: "2º Escaneo de Precedentes en Bóveda Local",
            desc: "Segundo, las espirales oculares consultan la Bóveda Markdown local buscando si este mismo problema jurídico ya cuenta con dictamen verificado.",
            color: "#34E8B0",
            svgOrigin: { x: 447, y: 412 }
        },
        3: {
            id: 3,
            shortLabel: "3/7 • Léxico BM25",
            badge: "ETAPA 3/7 • RECUPERACIÓN LÉXICA EXACTA",
            region: "Hemisferio Izquierdo • Circuito Esmeralda",
            title: "3º Rastreo Exacto de Artículos y Códigos (BM25)",
            desc: "Tercero, los flares recorren el hemisferio izquierdo esmeralda localizando coincidencias literales exactas de artículos, leyes y decretos vigentes.",
            color: "#34E8B0",
            svgOrigin: { x: 201, y: 242 }
        },
        4: {
            id: 4,
            shortLabel: "4/7 • Vectores BGE-M3",
            badge: "ETAPA 4/7 • EMBEBIMIENTO VECTORIAL DENSO",
            region: "Hemisferio Derecho • Circuito Zafiro",
            title: "4º Proyección Semántica Multidimensional (Embeddings)",
            desc: "Cuarto, el hemisferio derecho zafiro proyecta el significado profundo del caso en vectores matemáticos para hallar figuras jurídicas conexas.",
            color: "#38BDF8",
            svgOrigin: { x: 642, y: 205 }
        },
        5: {
            id: 5,
            shortLabel: "5/7 • Atención & RRF",
            badge: "ETAPA 5/7 • FUSIÓN RRF & ATENCIÓN DE CONTEXTO",
            region: "Tercer Ojo • Microprocesador Central",
            title: "5º Fusión RRF, Reranking y Lectura de Contexto",
            desc: "Quinto, el microchip frontal fusiona ambos hemisferios, invoca las nuevas normas aplicables y las inyecta por el pipeline estático hacia la ventana.",
            color: "#00E5FF",
            svgOrigin: { x: 391, y: 313 }
        },
        6: {
            id: 6,
            shortLabel: "6/7 • Generando Texto",
            badge: "ETAPA 6/7 • GENERACIÓN AUTOREGRESIVA EN ONDAS",
            region: "Corona Sináptica ➔ Pipeline de Datos",
            title: "6º Transmisión por Pipeline Sináptico (Onda 1 ➔ Onda 2)",
            desc: "Sexto, el flujo de datos viaja mediante flares luminosos a través del pipeline fijo conectado a la ventana: primero Veredicto, Fundamento y Subsunción; luego Ruta Procesal.",
            color: "#00E5FF",
            svgOrigin: { x: 721, y: 309 }
        },
        7: {
            id: 7,
            shortLabel: "7/7 • Grounding ✓",
            badge: "ETAPA 7/7 • AUDITORÍA ANTI-ALUCINACIONES",
            region: "Anillo Protector + Ojos del Tótem",
            title: "7º Verificación de Citas Normativas y Sello Final",
            desc: "Séptimo y último: se verifica matemáticamente que toda norma citada exista en las fuentes reales y los ojos del Tótem destellan sellando el precedente.",
            color: "#34E8B0",
            svgOrigin: { x: 447, y: 412 }
        }
    };

    /**
     * Caminos neuronales exactos en el espacio 782 x 1024 del arte oficial Sadigua.
     * Los flares luminosos recorren suavemente estas polilíneas (cero círculos rebotando).
     */
    const NEURAL_CIRCUIT_PATHS = {
        1: [
            [[391, 702], [391, 545]],
            [[318, 665], [318, 499], [368, 420]],
            [[469, 665], [469, 495], [418, 430]],
            [[248, 620], [248, 469], [305, 486]],
            [[540, 620], [540, 459], [483, 482]]
        ],
        2: [
            [[356, 431], [308, 431], [308, 395], [347, 395], [347, 411], [369, 402], [391, 352]],
            [[422, 431], [470, 431], [470, 395], [431, 395], [431, 412], [418, 394], [391, 352]]
        ],
        3: [
            [[143, 211], [201, 242], [318, 320], [356, 312]],
            [[286, 171], [315, 245], [362, 296]],
            [[142, 310], [245, 335], [337, 366], [362, 332]]
        ],
        4: [
            [[636, 112], [533, 111], [490, 174], [424, 296]],
            [[642, 205], [585, 242], [461, 320], [424, 312]],
            [[724, 252], [667, 243], [585, 242], [461, 366], [422, 330]]
        ],
        5: [
            [[201, 242], [318, 313], [356, 313], [356, 278], [426, 278], [426, 348], [356, 348]],
            [[642, 205], [466, 313], [426, 313], [426, 348], [356, 348], [356, 278], [426, 278]]
        ],
        6: [
            [[201, 242], [356, 312], [426, 312], [585, 242], [721, 309]],
            [[286, 171], [391, 278], [490, 174], [642, 205], [721, 309]],
            [[337, 366], [391, 348], [461, 366], [595, 335], [721, 309]]
        ],
        7: [
            [[88, 425], [160, 580], [278, 668], [391, 708], [504, 668], [622, 580], [694, 425]],
            [[34, 358], [92, 165], [240, 62], [391, 38], [542, 62], [690, 165], [748, 358]]
        ]
    };

    const ZONE_COLORS = {
        1: "#00E5FF",
        2: "#34E8B0",
        3: "#34E8B0",
        4: "#38BDF8",
        5: "#00E5FF",
        6: "#00E5FF",
        7: "#34E8B0"
    };

    class SadiguaNeuralVisualizer {
        constructor() {
            this.canvas = document.getElementById("synaptic-bridge-canvas");
            this.ctx = this.canvas ? this.canvas.getContext("2d") : null;
            this.stageEl = document.getElementById("brain-hologram-stage");
            this.svgEl = document.getElementById("brain-anatomy-svg");
            this.totemEyesEl = document.getElementById("totem-eyes-finale");
            this.badgeEl = document.getElementById("ped-layer-badge");
            this.regionEl = document.getElementById("ped-region-tag");
            this.titleEl = document.getElementById("ped-layer-title");
            this.descEl = document.getElementById("ped-layer-desc");
            this.stageStateText = document.getElementById("stage-state-text");
            this.stageLiveDot = document.getElementById("stage-live-dot");
            this.liveSpinner = document.getElementById("ped-live-spinner");
            this.headerBrainBtn = document.getElementById("btn-toggle-brain-stage");
            this.headerBrainLabel = document.getElementById("brain-stage-toggle-label");

            this.activeLayer = 0;
            this.secondaryZones = [];
            this.currentFlowStep = 0;
            this.currentSubSection = "";
            this.isProcessing = false;
            this.isStreamingWords = false;
            this.activeWave = 1;
            this.targetElement = null;

            this.pipelineFlares = [];
            this.sparks = [];
            this.neuralFlares = [];
            this.pipelineActiveAlpha = 0;
            this.portGlowAlpha = 0;
            this.eyeFlashAlpha = 0;
            this.pendingDocsCallback = null;
            this.phaseQueue = [];
            this.queueTimer = null;
            this.lastLayerSwitchAt = 0;
            this.lastPhotonAt = 0;
            this.lastFlareSpawnAt = 0;

            this._initResize();
            this._initInteractiveZones();
            this._animate = this._animate.bind(this);
            requestAnimationFrame(this._animate);
        }

        _initResize() {
            const resize = () => {
                if (!this.canvas) return;
                const dpr = Math.min(window.devicePixelRatio || 1, 2);
                this.canvas.width = Math.floor(window.innerWidth * dpr);
                this.canvas.height = Math.floor(window.innerHeight * dpr);
                if (this.ctx) {
                    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
                }
            };
            window.addEventListener("resize", resize);
            resize();
        }

        _initInteractiveZones() {
            document.querySelectorAll(".brain-zone").forEach((zoneEl) => {
                zoneEl.addEventListener("click", () => {
                    const z = parseInt(zoneEl.getAttribute("data-zone"), 10);
                    if (z >= 1 && z <= 7 && !this.isProcessing) {
                        this.inspectLayerManual(z);
                    }
                });
            });

            document.querySelectorAll(".layer-step-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    const z = parseInt(btn.getAttribute("data-layer"), 10);
                    if (z >= 1 && z <= 7 && !this.isProcessing) {
                        this.inspectLayerManual(z);
                    }
                });
            });
        }

        inspectLayerManual(layerNum) {
            this.secondaryZones = [];
            this._applyLayerVisuals(layerNum, { manual: true });
            this._burstZoneFlares(layerNum, 3);
            if (layerNum === 6) {
                this._spawnPipelineFlare({ color: "#00E5FF", speed: 0.032, label: "Flujo" });
            } else if (layerNum === 7) {
                this.triggerTotemEyeFlash();
            }
        }

        startSession(targetEl) {
            this._clearQueue();
            this.pendingDocsCallback = null;
            this.pipelineFlares = [];
            this.isProcessing = true;
            this.isStreamingWords = false;
            this.activeWave = 1;
            this.secondaryZones = [];
            this.currentSubSection = "";
            this.pipelineActiveAlpha = 0.25;
            this.portGlowAlpha = 0;
            this.setTargetElement(targetEl);

            if (this.totemEyesEl) {
                this.totemEyesEl.classList.remove("flash-active");
            }
            if (this.stageEl) this.stageEl.classList.add("active-processing");
            if (this.stageLiveDot) this.stageLiveDot.classList.add("processing");
            if (this.liveSpinner) this.liveSpinner.style.display = "inline-block";
            if (this.stageStateText) this.stageStateText.textContent = "SECUENCIA NEURONAL EN CURSO";

            document.querySelectorAll(".layer-step-btn").forEach((b) => {
                b.classList.remove("active", "completed");
            });
            this.setFlowStep(1);
        }

        /**
         * Sincroniza la aparición de los nuevos artículos verdes en el HUD exactamente cuando
         * el cerebro entra en la etapa de vectores / fusión RRF (o de inmediato si ya empezó a escribir).
         */
        scheduleDocsReveal(callback) {
            if (typeof callback !== "function") return;
            if (this.activeLayer >= 4 || this.isStreamingWords || !this.isProcessing) {
                this.pendingDocsCallback = null;
                callback();
            } else {
                this.pendingDocsCallback = callback;
            }
        }

        _flushPendingDocsIfReady(layerNum) {
            if (this.pendingDocsCallback && layerNum >= 4) {
                const cb = this.pendingDocsCallback;
                this.pendingDocsCallback = null;
                cb();
            }
        }

        setTargetElement(el) {
            if (this.targetElement && this.targetElement !== el) {
                this.targetElement.classList.remove("receiving-neural-stream");
            }
            this.targetElement = el || null;
        }

        /**
         * Actualiza el mapa secuencial "1. RAG -> 2. Veredicto -> 3. Fundamento -> 4. Subsunción -> 5. Ruta -> 6. Tutela & Sello"
         */
        setFlowStep(stepNum, allDone = false) {
            this.currentFlowStep = stepNum;
            document.querySelectorAll("#response-flow-track .flow-step").forEach((el) => {
                const n = parseInt(el.getAttribute("data-flow"), 10);
                el.classList.remove("active", "done");
                if (allDone || n < stepNum) {
                    el.classList.add("done");
                } else if (n === stepNum) {
                    el.classList.add("active");
                }
            });
        }

        /**
         * Cadencia pedagógica legible (~1.1s por etapa inicial 1..5) para que se observe con total claridad
         * qué va primero y qué va después antes de que empiece la escritura de palabras.
         */
        activateLayer(layerNum, options = {}) {
            const immediate = Boolean(options.immediate);
            if (immediate) {
                this._clearQueue();
                this._applyLayerVisuals(layerNum, options);
                return;
            }

            const now = performance.now();
            const minHoldMs = 1050;
            const elapsed = now - this.lastLayerSwitchAt;

            if (this.phaseQueue.length === 0 && elapsed >= minHoldMs) {
                this._applyLayerVisuals(layerNum, options);
            } else {
                const lastQueued = this.phaseQueue[this.phaseQueue.length - 1];
                if (!lastQueued || lastQueued.layerNum !== layerNum) {
                    this.phaseQueue.push({ layerNum, options });
                }
                this._scheduleQueueDrain(Math.max(160, minHoldMs - elapsed));
            }
        }

        _scheduleQueueDrain(delayMs) {
            if (this.queueTimer) return;
            this.queueTimer = setTimeout(() => {
                this.queueTimer = null;
                if (this.phaseQueue.length > 0) {
                    const next = this.phaseQueue.shift();
                    this._applyLayerVisuals(next.layerNum, next.options);
                    if (this.phaseQueue.length > 0) {
                        this._scheduleQueueDrain(1050);
                    }
                }
            }, delayMs);
        }

        _clearQueue() {
            this.phaseQueue = [];
            if (this.queueTimer) {
                clearTimeout(this.queueTimer);
                this.queueTimer = null;
            }
        }

        _syncZoneHighlights(primaryZone, extraZones = []) {
            if (this.stageEl) {
                this.stageEl.setAttribute("data-active-zone", String(primaryZone));
            }
            const litSet = new Set([primaryZone, ...extraZones]);
            document.querySelectorAll(".brain-zone").forEach((zEl) => {
                const z = parseInt(zEl.getAttribute("data-zone"), 10);
                zEl.classList.toggle("zone-lit", litSet.has(z));
            });
        }

        _updateHeaderStageButton(shortText, blinking) {
            if (!this.headerBrainBtn || !this.headerBrainLabel) return;
            const cockpit = document.getElementById("neural-cockpit");
            const isCollapsed = cockpit && cockpit.classList.contains("brain-collapsed");
            if (blinking) {
                this.headerBrainBtn.classList.add("stage-blinking");
                this.headerBrainLabel.textContent = shortText;
            } else {
                this.headerBrainBtn.classList.remove("stage-blinking");
                this.headerBrainLabel.textContent = isCollapsed ? "Mostrar Núcleo" : "Núcleo Activo";
            }
        }

        _applyLayerVisuals(layerNum, options = {}) {
            const info = COGNITIVE_LAYERS[layerNum];
            if (!info) return;

            this.activeLayer = layerNum;
            this.secondaryZones = options.secondaryZones || [];
            this.lastLayerSwitchAt = performance.now();

            const activeColor = options.color || (options.wave === 2 ? "#34E8B0" : info.color);
            document.documentElement.style.setProperty("--active-layer-color", activeColor);

            this._syncZoneHighlights(layerNum, this.secondaryZones);
            this._flushPendingDocsIfReady(layerNum);

            // Actualizar intermitencia en el botón superior de la etapa activa (1..7)
            const blinkLayerBtn = options.blinkButton || layerNum;
            document.querySelectorAll(".layer-step-btn").forEach((btn) => {
                const n = parseInt(btn.getAttribute("data-layer"), 10);
                btn.classList.remove("active");
                if (n < layerNum && !options.manual) {
                    btn.classList.add("completed");
                } else if (n === blinkLayerBtn) {
                    btn.classList.remove("completed");
                    btn.classList.add("active");
                } else if (options.manual) {
                    btn.classList.remove("completed");
                }
            });

            if (this.isProcessing) {
                this._updateHeaderStageButton(options.shortLabel || info.shortLabel, true);
            }

            if (this.badgeEl) {
                this.badgeEl.textContent = options.customBadge || info.badge;
                this.badgeEl.style.color = activeColor;
                this.badgeEl.style.borderColor = activeColor;
            }
            if (this.regionEl) {
                this.regionEl.textContent = options.customRegion || info.region;
            }
            if (this.titleEl) {
                this.titleEl.textContent = options.customTitle || info.title;
            }
            if (this.descEl) {
                this.descEl.textContent = options.customDesc || info.desc;
            }

            this._burstZoneFlares(layerNum, 2);
        }

        /**
         * Transición entre Onda 1 y Onda 2 ("Generando Onda 2..."):
         * El cerebro vuelve a Atención Central (Zona 5) mientras estructura la Ruta Procesal.
         */
        onWaveTransition() {
            this.isStreamingWords = false;
            this.pipelineActiveAlpha = 0.45;
            this.currentSubSection = "wave2_prep";
            this.setFlowStep(5);
            this.activateLayer(5, {
                immediate: true,
                secondaryZones: [3, 4],
                color: "#34E8B0",
                shortLabel: "5/7 • Generando Onda 2",
                customBadge: "TRANSICIÓN SINÁPTICA • GENERANDO ONDA 2",
                customRegion: "Microchip Central + Ambos Hemisferios",
                customTitle: "Estructurando Ruta Procesal, Tutela y Acciones Concretas",
                customDesc: "Concluido el dictamen sustancial (Onda 1), el procesador central re-enfoca las fuentes para transmitir por el pipeline la estrategia procesal (Onda 2)."
            });
        }

        /**
         * Analiza en O(1) sobre el tramo reciente qué sección del dictamen se está escribiendo y
         * alterna dinámicamente los circuitos neuronales colaborativos.
         */
        onTokenGenerated(accumulatedText = "", wave = 1) {
            this.activeWave = wave;
            this.isStreamingWords = true;
            this._flushPendingDocsIfReady(6);

            // Escaneo ligero sobre el tramo reciente sin bloquear el renderizado de texto
            const tail = accumulatedText.slice(-520).toLowerCase();
            let subKey = this.currentSubSection || (wave === 1 ? "w1_veredicto" : "w2_ruta");

            if (wave === 1) {
                if (!subKey.startsWith("w1_")) subKey = "w1_veredicto";
                if (tail.includes("subsunción") || tail.includes("análisis y subsun")) {
                    subKey = "w1_subsuncion";
                } else if (subKey !== "w1_subsuncion" && (tail.includes("fundamento normativo") || tail.includes("normativo aplicable"))) {
                    subKey = "w1_fundamento";
                }
            } else {
                if (!subKey.startsWith("w2_")) subKey = "w2_ruta";
                if (
                    tail.includes("acciones judiciales") ||
                    tail.includes("acción de tutela") ||
                    tail.includes("conclusión") ||
                    tail.includes("recomendaciones prácticas")
                ) {
                    subKey = "w2_tutela_cierre";
                }
            }

            if (this.currentSubSection !== subKey) {
                this.currentSubSection = subKey;
                let flowIdx = 2;
                let visualCfg = null;

                if (subKey === "w1_subsuncion") {
                    flowIdx = 4;
                    visualCfg = {
                        secondaryZones: [4, 5],
                        blinkButton: 6,
                        color: "#38BDF8",
                        shortLabel: "Onda 1 • 3º Subsunción",
                        customBadge: "ONDA 1 (3/3) • SUBSUNCIÓN JURÍDICA",
                        customRegion: "Hemisferio Zafiro (Vectores) ➔ Pipeline Estático",
                        customTitle: "3º Aplicando las Normas al Caso Concreto (Subsunción)",
                        customDesc: "Tras fijar el veredicto y citar la ley, el circuito vectorial derecho envía por el pipeline el cruce entre los hechos del usuario y la doctrina."
                    };
                } else if (subKey === "w1_fundamento") {
                    flowIdx = 3;
                    visualCfg = {
                        secondaryZones: [3, 5],
                        blinkButton: 6,
                        color: "#34E8B0",
                        shortLabel: "Onda 1 • 2º Fundamento",
                        customBadge: "ONDA 1 (2/3) • FUNDAMENTO NORMATIVO",
                        customRegion: "Hemisferio Esmeralda (BM25) ➔ Pipeline Estático",
                        customTitle: "2º Extrayendo y Explicando Artículos Vigentes",
                        customDesc: "El hemisferio izquierdo esmeralda inyecta hacia el pipeline los artículos literales verificados en BM25 para sustentar el veredicto."
                    };
                } else if (subKey === "w1_veredicto") {
                    flowIdx = 2;
                    visualCfg = {
                        secondaryZones: [5],
                        blinkButton: 6,
                        color: "#00E5FF",
                        shortLabel: "Onda 1 • 1º Veredicto",
                        customBadge: "ONDA 1 (1/3) • VEREDICTO DIRECTO",
                        customRegion: "Microchip Central ➔ Pipeline de Datos",
                        customTitle: "1º Emitiendo Veredicto Jurídico Frontal",
                        customDesc: "Primero se responde de forma directa el problema jurídico, transportando los pulsos de datos por el pipeline fijo hacia la ventana de texto."
                    };
                } else if (subKey === "w2_tutela_cierre") {
                    flowIdx = 6;
                    visualCfg = {
                        secondaryZones: [3, 4, 5],
                        blinkButton: 6,
                        color: "#34E8B0",
                        shortLabel: "Onda 2 • Tutela & Cierre",
                        customBadge: "ONDA 2 (2/2) • TUTELA, ACCIONES Y CIERRE",
                        customRegion: "Corona Sináptica Completa ➔ Pipeline Estático",
                        customTitle: "Última Fase Generativa: Acciones Constitucionales y Recomendaciones",
                        customDesc: "Ambos hemisferios convergen enviando el tramo final de Tutela, preservación probatoria y recomendaciones antes del sello anti-alucinación."
                    };
                } else {
                    flowIdx = 5;
                    visualCfg = {
                        secondaryZones: [3, 5],
                        blinkButton: 6,
                        color: "#34E8B0",
                        shortLabel: "Onda 2 • Ruta Procesal",
                        customBadge: "ONDA 2 (1/2) • RUTA PROCESAL PASO A PASO",
                        customRegion: "Núcleo Procesal ➔ Pipeline Esmeralda",
                        customTitle: "Redactando Ruta Procesal (Reclamación Previa y Entidades)",
                        customDesc: "El pipeline esmeralda transmite en orden cronológico qué actuación radicar primero, ante qué autoridad y bajo qué términos legales."
                    };
                }

                this.setFlowStep(flowIdx);
                this.activateLayer(6, Object.assign({ immediate: true, wave }, visualCfg));
            }

            this.emitTokenPhoton(wave);
        }

        emitContextBurst(documents = []) {
            const maxSeen = this.phaseQueue.reduce((m, item) => Math.max(m, item.layerNum), this.activeLayer);
            if (maxSeen < 4) this.activateLayer(4);
            if (maxSeen < 5) this.activateLayer(5);

            if (!this._isStageVisible()) return;
            this.pipelineActiveAlpha = Math.max(this.pipelineActiveAlpha, 0.85);

            const count = Math.max(2, Math.min(documents.length, 4));
            for (let i = 0; i < count; i++) {
                const doc = documents[i % Math.max(1, documents.length)];
                const label = doc ? (doc.articulo || doc.section || "Norma").slice(0, 15) : "Norma";
                setTimeout(() => {
                    this._spawnPipelineFlare({
                        color: i % 2 === 0 ? "#00E5FF" : "#34E8B0",
                        speed: 0.025,
                        label
                    });
                }, i * 165);
            }
        }

        emitTokenPhoton(wave = 1) {
            this.activeWave = wave;
            if (this.targetElement) {
                this.targetElement.classList.add("receiving-neural-stream");
            }
            const msgArea = document.getElementById("chat-messages");
            if (msgArea) msgArea.classList.add("receiving-pipeline-data");

            this.pipelineActiveAlpha = 1.0;

            const now = performance.now();
            if (now - this.lastPhotonAt < 75) return;
            this.lastPhotonAt = now;

            if (!this._isStageVisible()) return;
            const color = wave === 2 ? "#34E8B0" : "#00E5FF";

            this._spawnPipelineFlare({
                color,
                speed: 0.042 + Math.random() * 0.012,
                label: ""
            });
        }

        /**
         * Dispara el Flash y Glow final en ambos ojos espirales del Tótem Sadigua (331,411 y 447,412)
         */
        triggerTotemEyeFlash() {
            this.eyeFlashAlpha = 1.0;
            if (this.totemEyesEl) {
                this.totemEyesEl.classList.remove("flash-active");
                // Forzar reflow para reiniciar animación CSS limpiamente
                void this.totemEyesEl.offsetWidth;
                this.totemEyesEl.classList.add("flash-active");
            }
        }

        completeSession(options = {}) {
            this._clearQueue();
            this._flushPendingDocsIfReady(7);
            const isCacheHit = Boolean(options.cacheHit);
            this.isStreamingWords = false;

            if (isCacheHit) {
                this._applyLayerVisuals(2, {
                    secondaryZones: [7],
                    customBadge: "⚡ PRECEDENTE VERIFICADO EN BÓVEDA",
                    customRegion: "Ojos del Tótem • Memoria Obsidiana",
                    customTitle: "Recuperación Instantánea desde Memoria Obsidiana",
                    customDesc: "Los ojos del Tótem localizaron un precedente idéntico ya auditado en disco local, entregando el dictamen completo en 0.05s."
                });
                this._spawnPipelineFlare({ color: "#34E8B0", speed: 0.045, label: "Precedente" });
            } else {
                this._applyLayerVisuals(7, {
                    secondaryZones: [2],
                    customBadge: "✓ DICTAMEN SELLADO • GROUNDING VERIFICADO",
                    customRegion: "Ojos del Tótem + Anillo Anti-Alucinaciones"
                });
            }

            this.setFlowStep(6, true);
            this.isProcessing = false;
            this._updateHeaderStageButton("Núcleo Activo", false);

            document.querySelectorAll(".layer-step-btn").forEach((b) => {
                b.classList.remove("active");
                b.classList.add("completed");
            });

            if (this.liveSpinner) this.liveSpinner.style.display = "none";
            if (this.stageLiveDot) this.stageLiveDot.classList.remove("processing");
            if (this.stageStateText) {
                this.stageStateText.textContent = isCacheHit
                    ? "⚡ PRECEDENTE ENTREGADO (0.05s)"
                    : "✓ DICTAMEN AUDITADO Y SELLADO";
            }

            // ¡FLASH FINAL EN LOS OJOS DEL TÓTEM!
            this.triggerTotemEyeFlash();

            setTimeout(() => {
                if (!this.isProcessing) {
                    if (this.stageEl) this.stageEl.classList.remove("active-processing");
                    if (this.targetElement) {
                        this.targetElement.classList.remove("receiving-neural-stream");
                    }
                    const msgArea = document.getElementById("chat-messages");
                    if (msgArea) msgArea.classList.remove("receiving-pipeline-data");
                }
            }, 2200);
        }

        handleError() {
            this._clearQueue();
            this.pendingDocsCallback = null;
            this.isProcessing = false;
            this.isStreamingWords = false;
            this._updateHeaderStageButton("Núcleo Activo", false);
            if (this.liveSpinner) this.liveSpinner.style.display = "none";
            if (this.stageLiveDot) this.stageLiveDot.classList.remove("processing");
            if (this.stageEl) this.stageEl.classList.remove("active-processing");
            if (this.targetElement) this.targetElement.classList.remove("receiving-neural-stream");
            const msgArea = document.getElementById("chat-messages");
            if (msgArea) msgArea.classList.remove("receiving-pipeline-data");
            if (this.stageStateText) this.stageStateText.textContent = "ALERTA EN PROCESAMIENTO";
        }

        _isStageVisible() {
            const tabChat = document.getElementById("tab-chat");
            const cockpit = document.getElementById("neural-cockpit");
            if (!tabChat || !tabChat.classList.contains("active")) return false;
            if (cockpit && cockpit.classList.contains("brain-collapsed")) return false;
            if (!this.svgEl) return false;
            const r = this.svgEl.getBoundingClientRect();
            return r.width > 20 && r.height > 20;
        }

        _svgToScreen(svgX, svgY) {
            if (!this.svgEl) return null;
            const rect = this.svgEl.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) return null;
            return {
                x: rect.left + (svgX / 782) * rect.width,
                y: rect.top + (svgY / 1024) * rect.height
            };
        }

        getBrainScreenOrigin(layerNum) {
            const info = COGNITIVE_LAYERS[layerNum] || COGNITIVE_LAYERS[6];
            return this._svgToScreen(info.svgOrigin.x, info.svgOrigin.y);
        }

        /**
         * Calcula la geometría 100% ESTÁTICA del Pipeline Sináptico que conecta el terminal
         * derecho del Cerebro (721, 309) con el puerto fijo de entrada de la Ventana de Texto
         * (#chat-messages), SIN perseguir jamás al texto ni moverse al hacer scroll.
         */
        _getStaticPipelinePoints() {
            const origin = this._svgToScreen(721, 309);
            const msgWindow = document.getElementById("chat-messages") || document.getElementById("chat-context-window");
            if (!origin || !msgWindow) return null;

            const winRect = msgWindow.getBoundingClientRect();
            if (winRect.width < 20 || winRect.height < 20) return null;

            // Diseño lado a lado (Desktop): puente de circuito impreso (PCB) fijo hacia el borde izquierdo de la ventana
            if (winRect.left > origin.x + 14) {
                const dockX = winRect.left;
                const portY = Math.min(Math.max(origin.y + 18, winRect.top + 36), winRect.bottom - 36);
                const spanX = dockX - origin.x;

                return [
                    { x: origin.x, y: origin.y },
                    { x: origin.x + spanX * 0.42, y: origin.y },
                    { x: origin.x + spanX * 0.62, y: portY },
                    { x: dockX, y: portY }
                ];
            }

            // Vista apilada (Móvil / pantallas estrechas): conducto vertical fijo
            const collarOrigin = this._svgToScreen(391, 708) || origin;
            if (winRect.top > collarOrigin.y + 6) {
                return [
                    { x: collarOrigin.x, y: collarOrigin.y },
                    { x: collarOrigin.x, y: winRect.top }
                ];
            }

            return null;
        }

        _pointAlongScreenPolyline(points, t) {
            if (!points || points.length === 0) return null;
            if (points.length === 1) return { x: points[0].x, y: points[0].y, angle: 0 };

            let totalLen = 0;
            const segLens = [];
            for (let i = 1; i < points.length; i++) {
                const len = Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y);
                segLens.push(len);
                totalLen += len;
            }
            if (totalLen === 0) return { x: points[0].x, y: points[0].y, angle: 0 };

            let targetDist = Math.max(0, Math.min(1, t)) * totalLen;
            for (let i = 0; i < segLens.length; i++) {
                if (targetDist <= segLens[i] || i === segLens.length - 1) {
                    const localT = segLens[i] > 0 ? targetDist / segLens[i] : 0;
                    const x = points[i].x + (points[i + 1].x - points[i].x) * localT;
                    const y = points[i].y + (points[i + 1].y - points[i].y) * localT;
                    const angle = Math.atan2(points[i + 1].y - points[i].y, points[i + 1].x - points[i].x);
                    return { x, y, angle };
                }
                targetDist -= segLens[i];
            }
            const last = points[points.length - 1];
            return { x: last.x, y: last.y, angle: 0 };
        }

        /**
         * Genera flares estilizados que viajan a lo largo de los caminos neuronales reales del cerebro
         */
        _burstZoneFlares(zoneId, multiplier = 1) {
            const paths = NEURAL_CIRCUIT_PATHS[zoneId];
            if (!paths || !this._isStageVisible()) return;
            const color = ZONE_COLORS[zoneId] || "#00E5FF";

            for (let m = 0; m < multiplier; m++) {
                paths.forEach((poly, idx) => {
                    if (this.neuralFlares.length > 26) return;
                    this.neuralFlares.push({
                        points: poly,
                        progress: (m * 0.35 + idx * 0.14) % 0.85,
                        speed: 0.014 + Math.random() * 0.008,
                        color,
                        trail: []
                    });
                });
            }
        }

        _maintainActiveNeuralFlares(now) {
            if (!this._isStageVisible()) return;
            const activeZones = [];
            if (this.activeLayer >= 1 && this.activeLayer <= 7) {
                activeZones.push(this.activeLayer);
            }
            for (const z of this.secondaryZones) {
                if (!activeZones.includes(z)) activeZones.push(z);
            }
            if (activeZones.length === 0) return;

            const intervalMs = this.isProcessing ? 340 : 950;
            if (now - this.lastFlareSpawnAt < intervalMs) return;
            this.lastFlareSpawnAt = now;

            const zonePick = activeZones[Math.floor(Math.random() * activeZones.length)];
            const paths = NEURAL_CIRCUIT_PATHS[zonePick];
            if (!paths || paths.length === 0 || this.neuralFlares.length > 22) return;

            const poly = paths[Math.floor(Math.random() * paths.length)];
            const color = (zonePick === 6 && this.activeWave === 2)
                ? "#34E8B0"
                : (ZONE_COLORS[zonePick] || "#00E5FF");

            this.neuralFlares.push({
                points: poly,
                progress: 0,
                speed: this.isProcessing ? (0.016 + Math.random() * 0.009) : 0.011,
                color,
                trail: []
            });
        }

        _pointAlongPolyline(points, t) {
            if (!points || points.length === 0) return null;
            if (points.length === 1) return this._svgToScreen(points[0][0], points[0][1]);

            let totalLen = 0;
            const segLens = [];
            for (let i = 1; i < points.length; i++) {
                const dx = points[i][0] - points[i - 1][0];
                const dy = points[i][1] - points[i - 1][1];
                const len = Math.hypot(dx, dy);
                segLens.push(len);
                totalLen += len;
            }
            if (totalLen === 0) return this._svgToScreen(points[0][0], points[0][1]);

            let targetDist = Math.max(0, Math.min(1, t)) * totalLen;
            for (let i = 0; i < segLens.length; i++) {
                if (targetDist <= segLens[i] || i === segLens.length - 1) {
                    const localT = segLens[i] > 0 ? targetDist / segLens[i] : 0;
                    const sx = points[i][0] + (points[i + 1][0] - points[i][0]) * localT;
                    const sy = points[i][1] + (points[i + 1][1] - points[i][1]) * localT;
                    return this._svgToScreen(sx, sy);
                }
                targetDist -= segLens[i];
            }
            return this._svgToScreen(points[points.length - 1][0], points[points.length - 1][1]);
        }

        _updateAndDrawNeuralFlares() {
            if (!this.ctx) return;
            for (let i = this.neuralFlares.length - 1; i >= 0; i--) {
                const f = this.neuralFlares[i];
                f.progress += f.speed;

                const pos = this._pointAlongPolyline(f.points, Math.min(1, f.progress));
                if (pos) {
                    f.trail.push(pos);
                    if (f.trail.length > 13) f.trail.shift();
                }

                // Estela afilada tipo cometa recorriendo la traza neuronal
                if (f.trail.length > 1) {
                    this.ctx.save();
                    for (let j = 1; j < f.trail.length; j++) {
                        const ratio = j / f.trail.length;
                        this.ctx.beginPath();
                        this.ctx.moveTo(f.trail[j - 1].x, f.trail[j - 1].y);
                        this.ctx.lineTo(f.trail[j].x, f.trail[j].y);
                        this.ctx.strokeStyle = j > f.trail.length - 3 ? "#FFFFFF" : f.color;
                        this.ctx.globalAlpha = ratio * 0.85;
                        this.ctx.lineWidth = 0.8 + ratio * 2.8;
                        this.ctx.lineCap = "round";
                        this.ctx.shadowBlur = 10;
                        this.ctx.shadowColor = f.color;
                        this.ctx.stroke();
                    }

                    // Destello estelar fino (flare cruzado sin círculos pesados) en la punta
                    const head = f.trail[f.trail.length - 1];
                    const prev = f.trail[f.trail.length - 2];
                    const angle = Math.atan2(head.y - prev.y, head.x - prev.x);
                    this._drawSharpStarFlare(head.x, head.y, 7.5, f.color, angle);
                    this.ctx.restore();
                }

                if (f.progress >= 1.06) {
                    this.neuralFlares.splice(i, 1);
                }
            }
        }

        _drawSharpStarFlare(x, y, armLen, color, angle = 0) {
            if (!this.ctx) return;
            this.ctx.save();
            this.ctx.translate(x, y);
            this.ctx.rotate(angle);
            this.ctx.strokeStyle = "#FFFFFF";
            this.ctx.shadowBlur = 12;
            this.ctx.shadowColor = color;
            this.ctx.lineWidth = 1.5;
            this.ctx.beginPath();
            this.ctx.moveTo(-armLen, 0);
            this.ctx.lineTo(armLen, 0);
            this.ctx.moveTo(0, -armLen * 0.55);
            this.ctx.lineTo(0, armLen * 0.55);
            this.ctx.stroke();
            this.ctx.restore();
        }

        /**
         * Dibuja el Pipeline Sináptico ESTÁTICO acoplado entre el Cerebro y el borde izquierdo
         * de la Ventana de Texto. Su geometría permanece completamente inmóvil.
         */
        _drawStaticPipeline(points) {
            if (!this.ctx || !points || points.length < 2) return;

            if (!this.isStreamingWords) {
                this.pipelineActiveAlpha *= this.isProcessing ? 0.97 : 0.92;
            }
            this.portGlowAlpha *= 0.9;

            const activeBoost = Math.max(0, Math.min(1, this.pipelineActiveAlpha));
            const mainColor = this.activeWave === 2 ? "#34E8B0" : "#00E5FF";
            const startPt = points[0];
            const endPt = points[points.length - 1];

            this.ctx.save();

            // 1. Canaleta exterior blindada del Pipeline (inmóvil)
            this.ctx.beginPath();
            this.ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                this.ctx.lineTo(points[i].x, points[i].y);
            }
            this.ctx.strokeStyle = mainColor;
            this.ctx.globalAlpha = 0.09 + activeBoost * 0.16;
            this.ctx.lineWidth = 8;
            this.ctx.lineCap = "butt";
            this.ctx.lineJoin = "round";
            if (activeBoost > 0.15) {
                this.ctx.shadowBlur = 14;
                this.ctx.shadowColor = mainColor;
            }
            this.ctx.stroke();

            // 2. Riel central fijo de circuito impreso (PCB)
            this.ctx.shadowBlur = 0;
            this.ctx.beginPath();
            this.ctx.moveTo(points[0].x, points[0].y);
            for (let i = 1; i < points.length; i++) {
                this.ctx.lineTo(points[i].x, points[i].y);
            }
            this.ctx.strokeStyle = activeBoost > 0.2 ? "#CCF7FF" : "#38BDF8";
            this.ctx.globalAlpha = 0.28 + activeBoost * 0.45;
            this.ctx.lineWidth = 1.7;
            this.ctx.stroke();

            // 3. Terminal geométrico fijo en el Cerebro (rombo Muisca estático, sin círculos)
            this.ctx.globalAlpha = 0.55 + activeBoost * 0.45;
            this.ctx.fillStyle = mainColor;
            this.ctx.beginPath();
            this.ctx.moveTo(startPt.x, startPt.y - 4.5);
            this.ctx.lineTo(startPt.x + 4.5, startPt.y);
            this.ctx.lineTo(startPt.x, startPt.y + 4.5);
            this.ctx.lineTo(startPt.x - 4.5, startPt.y);
            this.ctx.closePath();
            this.ctx.fill();

            // 4. Conector / Puerto fijo acoplado al marco de la Ventana de Texto (inmóvil)
            const portHighlight = Math.max(activeBoost * 0.55, this.portGlowAlpha);
            this.ctx.globalAlpha = 0.42 + portHighlight * 0.58;
            this.ctx.strokeStyle = this.portGlowAlpha > 0.25 ? "#FFFFFF" : mainColor;
            this.ctx.lineWidth = 2.6;
            if (this.portGlowAlpha > 0.1) {
                this.ctx.shadowBlur = 14;
                this.ctx.shadowColor = mainColor;
            }
            this.ctx.beginPath();
            this.ctx.moveTo(endPt.x, endPt.y - 9);
            this.ctx.lineTo(endPt.x, endPt.y + 9);
            // Pequeñas pestañas de anclaje hacia la ventana
            this.ctx.moveTo(endPt.x, endPt.y - 9);
            this.ctx.lineTo(endPt.x + 5, endPt.y - 9);
            this.ctx.moveTo(endPt.x, endPt.y + 9);
            this.ctx.lineTo(endPt.x + 5, endPt.y + 9);
            this.ctx.stroke();

            this.ctx.restore();
        }

        _spawnPipelineFlare(cfg = {}) {
            if (this.pipelineFlares.length > 18) return;
            this.pipelineFlares.push({
                progress: 0,
                speed: cfg.speed || 0.04,
                color: cfg.color || "#00E5FF",
                label: cfg.label || ""
            });
        }

        /**
         * Anima los Flares bioluminiscentes deslizándose estrictamente por dentro del
         * Pipeline Estático hacia la ventana de texto.
         */
        _updateAndDrawPipelineFlares(points) {
            if (!this.ctx || !points || points.length < 2) {
                this.pipelineFlares = [];
                return;
            }

            for (let i = this.pipelineFlares.length - 1; i >= 0; i--) {
                const fl = this.pipelineFlares[i];
                fl.progress += fl.speed;

                const headT = Math.min(1, fl.progress);
                const tailSpan = 0.22;
                const tailT = Math.max(0, fl.progress - tailSpan);
                const steps = 10;

                if (headT > tailT) {
                    this.ctx.save();
                    let prevPt = this._pointAlongScreenPolyline(points, tailT);

                    for (let s = 1; s <= steps; s++) {
                        const ratio = s / steps;
                        const sampleT = tailT + (headT - tailT) * ratio;
                        const curPt = this._pointAlongScreenPolyline(points, sampleT);
                        if (prevPt && curPt) {
                            this.ctx.beginPath();
                            this.ctx.moveTo(prevPt.x, prevPt.y);
                            this.ctx.lineTo(curPt.x, curPt.y);
                            this.ctx.strokeStyle = ratio > 0.8 ? "#FFFFFF" : fl.color;
                            this.ctx.globalAlpha = ratio * 0.92;
                            this.ctx.lineWidth = 1.2 + ratio * 3.4;
                            this.ctx.lineCap = "round";
                            this.ctx.shadowBlur = 12;
                            this.ctx.shadowColor = fl.color;
                            this.ctx.stroke();
                        }
                        prevPt = curPt;
                    }

                    const headPt = this._pointAlongScreenPolyline(points, headT);
                    if (headPt) {
                        this._drawSharpStarFlare(headPt.x, headPt.y, 8.5, fl.color, headPt.angle);
                        if (fl.label && headT < 0.95) {
                            this.ctx.shadowBlur = 0;
                            this.ctx.globalAlpha = 0.92;
                            this.ctx.font = "700 10px 'Segoe UI', sans-serif";
                            this.ctx.fillStyle = "#ECF8FF";
                            this.ctx.fillText(fl.label, headPt.x - 16, headPt.y - 10);
                        }
                    }
                    this.ctx.restore();
                }

                if (fl.progress >= 1.04) {
                    const endPt = points[points.length - 1];
                    this.portGlowAlpha = 1.0;
                    this._spawnImpactSparks(endPt.x + 2, endPt.y, fl.color, 3);
                    this.pipelineFlares.splice(i, 1);
                }
            }
        }

        _spawnImpactSparks(x, y, color, count = 3) {
            for (let i = 0; i < count; i++) {
                const angle = (Math.random() - 0.5) * 1.1; // Hacia adentro del puerto de la ventana
                const spd = 0.9 + Math.random() * 1.8;
                this.sparks.push({
                    x,
                    y,
                    vx: Math.cos(angle) * spd,
                    vy: Math.sin(angle) * spd,
                    alpha: 0.85,
                    color
                });
            }
        }

        _updateAndDrawSparks() {
            if (!this.ctx) return;
            for (let i = this.sparks.length - 1; i >= 0; i--) {
                const sp = this.sparks[i];
                const prevX = sp.x;
                const prevY = sp.y;
                sp.x += sp.vx;
                sp.y += sp.vy;
                sp.alpha -= 0.075;

                if (sp.alpha <= 0) {
                    this.sparks.splice(i, 1);
                    continue;
                }

                this.ctx.save();
                this.ctx.globalAlpha = sp.alpha;
                this.ctx.strokeStyle = sp.color;
                this.ctx.lineWidth = 1.4;
                this.ctx.beginPath();
                this.ctx.moveTo(prevX, prevY);
                this.ctx.lineTo(sp.x, sp.y);
                this.ctx.stroke();
                this.ctx.restore();
            }
        }

        /**
         * Destello óptico anamórfico en los dos ojos del Tótem Sadigua al concluir la respuesta
         */
        _drawTotemEyesCanvasFlash() {
            if (this.eyeFlashAlpha <= 0.01 || !this.ctx || !this._isStageVisible()) return;
            this.eyeFlashAlpha *= 0.955;

            const leftEye = this._svgToScreen(331, 411);
            const rightEye = this._svgToScreen(447, 412);
            if (!leftEye || !rightEye) return;

            const eyeDist = Math.hypot(rightEye.x - leftEye.x, rightEye.y - leftEye.y);
            const flareRadius = Math.max(26, eyeDist * 0.62) * (0.75 + this.eyeFlashAlpha * 0.45);
            const streakHalfWidth = eyeDist * (0.9 + this.eyeFlashAlpha * 1.15);

            this.ctx.save();
            this.ctx.globalCompositeOperation = "lighter";

            [leftEye, rightEye].forEach((eye) => {
                // Resplandor radial bioluminiscente sobre cada ojo del Tótem
                const g = this.ctx.createRadialGradient(eye.x, eye.y, 1, eye.x, eye.y, flareRadius);
                g.addColorStop(0, `rgba(255, 255, 255, ${Math.min(1, this.eyeFlashAlpha * 1.15)})`);
                g.addColorStop(0.28, `rgba(0, 229, 255, ${this.eyeFlashAlpha * 0.85})`);
                g.addColorStop(0.62, `rgba(52, 232, 176, ${this.eyeFlashAlpha * 0.45})`);
                g.addColorStop(1, "rgba(0, 229, 255, 0)");

                this.ctx.fillStyle = g;
                this.ctx.beginPath();
                this.ctx.arc(eye.x, eye.y, flareRadius, 0, Math.PI * 2);
                this.ctx.fill();

                // Destello horizontal anamórfico tipo cine
                const sg = this.ctx.createLinearGradient(eye.x - streakHalfWidth, eye.y, eye.x + streakHalfWidth, eye.y);
                sg.addColorStop(0, "rgba(0, 229, 255, 0)");
                sg.addColorStop(0.35, `rgba(52, 232, 176, ${this.eyeFlashAlpha * 0.7})`);
                sg.addColorStop(0.5, `rgba(255, 255, 255, ${Math.min(1, this.eyeFlashAlpha * 1.2)})`);
                sg.addColorStop(0.65, `rgba(0, 229, 255, ${this.eyeFlashAlpha * 0.7})`);
                sg.addColorStop(1, "rgba(0, 229, 255, 0)");

                this.ctx.strokeStyle = sg;
                this.ctx.lineWidth = 2.5 + this.eyeFlashAlpha * 4;
                this.ctx.beginPath();
                this.ctx.moveTo(eye.x - streakHalfWidth, eye.y);
                this.ctx.lineTo(eye.x + streakHalfWidth, eye.y);
                this.ctx.stroke();
            });

            this.ctx.restore();
        }

        _animate(now) {
            if (this.ctx && this.canvas) {
                this.ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

                if (this._isStageVisible()) {
                    const pipelinePts = this._getStaticPipelinePoints();
                    this._drawStaticPipeline(pipelinePts);
                    this._maintainActiveNeuralFlares(now);
                    this._updateAndDrawNeuralFlares();
                    this._updateAndDrawPipelineFlares(pipelinePts);
                    this._drawTotemEyesCanvasFlash();
                }
                this._updateAndDrawSparks();
            }
            requestAnimationFrame(this._animate);
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        window.sadiguaVisualizer = new SadiguaNeuralVisualizer();
    });
})();
