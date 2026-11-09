# SADIGUA (Cerebro Bochica)
## Shell Soberano de Inteligencia Artificial, RAG Anti-Alucinaciones & Memoria Obsidiano

> **Sadigua** es un sistema operativo cognitivo desacoplado y 100% soberano diseñado para correr en hardware local (desde laptops modestas hasta servidores on-premise) con **costo cero de inferencia**, **cero fuga de datos** y **estricto control fáctico contra alucinaciones**.

---

## 🚀 Portabilidad Extrema (< 1 MB)

El código fuente, la interfaz gráfica web SPA, los cartuchos normativos y el motor RAG ocupan **únicamente ~650 KB**.
- **Los modelos neuronales pesados (GGUF)** se gestionan de forma desacoplada y externa mediante el motor local **Ollama** o contenedores Docker.
- No se clonan gigabytes innecesarios en el repositorio de Git ni en carpetas compartidas de nube.

---

## 🏛️ Características Principales

1. **Inferencia Local Soberana**:
   - Optimizado para CPUs multinúcleo con aceleración vectorial **AVX2 / AVX-VNNI** y alta memoria RAM.
   - Modelo calibrado por defecto: **`qwen2.5:7b-instruct`** o **`qwen2.5:14b-instruct`** (calidad jurídica sobresaliente en español).
2. **Compuerta de Soberanía (*Air-Gap Gate*)**:
   - Inicia **100% desconectado de internet por defecto** (`CLOUD_EGRESS_ENABLED=False`).
   - Cumplimiento estricto del régimen de protección de datos personales (Ley 1581 de 2012 / Conpes 4144) y secreto profesional.
   - Permite conmutar opcionalmente a **Google Gemini** mediante autorización explícita en el panel de control.
3. **Pipeline RAG Quirúrgico de 8 Etapas**:
   - **Chunking Jerárquico Legal**: Preserva la estructura Libro > Título > Capítulo > Artículo.
   - **Búsqueda Híbrida**: Índice invertido literal **BM25 Okapi** + Vectores densos semánticos.
   - **Fusión RRF (k=60)** y **Reranker Neural de Precisión**.
   - **Validador de Grounding (Self-RAG)**: Bloquea respuestas que contengan artículos de ley inventados.
4. **Memoria Persistente 'Cerebro Obsidiano'**:
   - Bóveda de archivos Markdown estándar (`vault/`) con metadatos YAML y enlaces bidireccionales `[[wiki]]`.
   - 100% inspeccionable y editable desde la aplicación gratuita de escritorio [Obsidian](https://obsidian.md).
5. **Autodetección y Reconfiguración de Hardware (`HardwareProfiler`)**:
   - Al arrancar en cualquier equipo nuevo, analiza en tiempo real la topología de la CPU (núcleos/hilos), la RAM disponible y presencia de GPUs para autocalibrar los recursos óptimos.
6. **Interfaz Web Corporativa Moderna**:
   - Diseñada en **azul, gris y blanco** (cero modo oscuro) servida en el puerto **`7837`**.

---

## 🛠️ Instalación y Puesta en Marcha Rápida

### Requisitos Previos:
- Python 3.10 o superior.
- Git.
- [Ollama para Windows/Linux/Mac](https://ollama.com) (o Docker Desktop).

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/zergiobg/Sadigua-.git
cd Sadigua-
```

### Paso 2: Configurar el Entorno Virtual e Instalar Dependencias
```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
```

### Paso 3: Descargar y Sincronizar el Modelo Local (Ollama)
Sadigua se vincula automáticamente con el motor local Ollama que corre en `http://localhost:11434`:
```bash
# Descargar el modelo local calibrado (4.7 GB):
ollama pull qwen2.5:7b-instruct

# O si tienes 32 GB o más de memoria RAM (modelo 14B):
# ollama pull qwen2.5:14b-instruct
```

### Paso 4: Iniciar la Interfaz Web y Gateway
```bash
python sadigua.py web
```
Abre tu navegador en:
👉 **`http://localhost:7837`**

---

## 📂 Estructura del Proyecto

```
Cerebro/
├── .gitignore                       # Filtro estricto para no subir binarios pesados ni claves
├── .env.example                     # Plantilla de configuración
├── Dockerfile                       # Contenedor backend
├── docker-compose.yml               # Orquestación (Ollama + ChromaDB + Backend)
├── requirements.txt                 # Dependencias Python
├── README.md                        # Esta documentación
├── sadigua.py                       # CLI unificado (web, chat, ingest, vault, info)
│
├── config/                          # Parámetros del sistema y settings
│   └── settings.py
│
├── core/                            # Núcleo desacoplado de la IA
│   ├── engine/                      # Inferencia (LocalEngine y GeminiEngine)
│   ├── rag/                         # Ingestión, Chunking jerárquico, BM25, Vectores, RRF
│   ├── memory/                      # Gestor de Bóveda Obsidian y buffer de sesión
│   ├── agents/                      # Orquestador cognitivo y validador de grounding
│   ├── hardware/                    # Autodetector y calibrador dinámico de CPU/RAM
│   └── cartridges/                  # Gestor de cartuchos de dominio
│
├── cartridges/                      # Cartuchos intercambiables de conocimiento
│   ├── legal_co/                    # Cartucho Jurídico & Litigio (Constitución, CGP, Ley 1581)
│   └── telco_crm/                   # Cartucho CRM Telecomunicaciones (ETB, CRC 5111)
│
├── gateway/                         # Capa de exposición de servicios
│   ├── api.py                       # Backend REST & SSE (FastAPI en puerto 7837)
│   └── anonymizer.py                # Filtro de anonimización PII (Ley 1581)
│
├── web/                             # Frontend Gráfico SPA (Azul, Gris, Blanco)
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
│
├── vault/                           # Bóveda Obsidian activa (Expedientes y Clientes)
│   ├── expedientes/
│   └── clientes/
│
└── tests/                           # Banco de pruebas automatizado
    ├── test_sadigua_core.py
    ├── test_api_endpoints.py
    └── run_tests.py
```

---

## 🔒 Privacidad y Gobernanza de Datos

Sadigua fue concebido bajo el principio de **Privacidad desde el Diseño (Privacy by Design)**:
- Los expedientes de clientes y consultas legales **nunca salen de la memoria volátil de tu computador**.
- Incluye anonimizador de datos personales sensibles (PII) que enmascara cédulas, teléfonos y correos electrónicos antes de ser procesados.
- Cumple con las exigencias del **CONPES 4144** sobre soberanía de inteligencia artificial y la **Ley Estatutaria 1581 de 2012**.
