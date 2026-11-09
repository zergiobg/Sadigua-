# =====================================================================
# SADIGUA - SCRIPT DE MONTAJE Y DESPLIEGUE AUTOMATIZADO ("deploy Sadigua")
# =====================================================================

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       SADIGUA - DESPLIEGUE SOBERANO LOCAL DE ALTA PRECISIÓN     " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$baseDir = Split-Path -Parent $PSScriptRoot
Set-Location $baseDir

# -------------------------------------------------------------
# PASO 1: VERIFICACIÓN DE DEPENDENCIAS PYTHON
# -------------------------------------------------------------
Write-Host "`n[1/6] Verificando dependencias de Python..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
Write-Host "[OK] Dependencias instaladas y actualizadas." -ForegroundColor Green

# -------------------------------------------------------------
# PASO 2: VERIFICAR E INSTALAR OLLAMA
# -------------------------------------------------------------
Write-Host "`n[2/6] Verificando motor de inferencia local (Ollama)..." -ForegroundColor Yellow
$ollamaCmd = Get-Command "ollama" -ErrorAction SilentlyContinue
$ollamaExePath = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"

if (-not $ollamaCmd -and -not (Test-Path $ollamaExePath)) {
    Write-Host "[*] Ollama no encontrado. Instalando mediante winget..." -ForegroundColor Cyan
    winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements
    Start-Sleep -Seconds 5
}
Write-Host "[OK] Motor local Ollama verificado." -ForegroundColor Green

# -------------------------------------------------------------
# PASO 3: INICIAR SERVICIO OLLAMA EN SEGUNDO PLANO
# -------------------------------------------------------------
Write-Host "`n[3/6] Comprobando servicio Ollama en localhost:11434..." -ForegroundColor Yellow
$ollamaProc = Get-Process -Name "*ollama*" -ErrorAction SilentlyContinue
if (-not $ollamaProc) {
    Write-Host "[*] Iniciando daemon de Ollama en segundo plano..." -ForegroundColor Cyan
    if (Test-Path $ollamaExePath) {
        Start-Process $ollamaExePath -ArgumentList "serve" -WindowStyle Hidden
    } else {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    }
    Start-Sleep -Seconds 4
}
Write-Host "[OK] Servicio Ollama activo y escuchando." -ForegroundColor Green

# -------------------------------------------------------------
# PASO 4: PERFILADO DE HARDWARE Y DESCARGA DE MODELO
# -------------------------------------------------------------
Write-Host "`n[4/6] Diagnosticando hardware anfitrión y calibrando modelo..." -ForegroundColor Yellow
$profileJson = python -c "from core.hardware.detector import HardwareProfiler; import json; print(json.dumps(HardwareProfiler.profile()))" | Out-String | ConvertFrom-Json

Write-Host "     -> CPU Lógica: $($profileJson.logical_cores) hilos | Hilos Asignados: $($profileJson.optimal_threads)" -ForegroundColor Gray
Write-Host "     -> Memoria RAM: $($profileJson.ram_total_gb) GB Total ($($profileJson.ram_available_gb) GB Libre)" -ForegroundColor Gray
Write-Host "     -> Tier Detectado: $($profileJson.hardware_tier)" -ForegroundColor Gray

$targetModel = $profileJson.recommendations.active_model
if (-not $targetModel) { $targetModel = "qwen2.5:7b-instruct" }

Write-Host "[*] Modelo calibrado para este equipo: '$targetModel'..." -ForegroundColor Cyan

# Comprobar si el modelo ya está descargado
$installedModels = python -c "import httpx; r = httpx.get('http://localhost:11434/api/tags'); print([m['name'] for m in r.json().get('models', [])])" | Out-String

if ($installedModels -match $targetModel) {
    Write-Host "[OK] El modelo '$targetModel' ya está descargado en este equipo." -ForegroundColor Green
} else {
    Write-Host "[*] Descargando pesos matemáticos del modelo '$targetModel'..." -ForegroundColor Cyan
    if (Test-Path $ollamaExePath) {
        & $ollamaExePath pull $targetModel
    } else {
        ollama pull $targetModel
    }
    Write-Host "[OK] Modelo '$targetModel' listo en memoria." -ForegroundColor Green
}

# -------------------------------------------------------------
# PASO 5: RE-INDEXACIÓN INICIAL DEL CORPUS RAG
# -------------------------------------------------------------
Write-Host "`n[5/6] Indexando fuentes normativas y Bóveda Obsidian..." -ForegroundColor Yellow
python sadigua.py ingest
Write-Host "[OK] Fragmentos jurídicos y base vectorial sincronizados." -ForegroundColor Green

# -------------------------------------------------------------
# PASO 6: LANZAMIENTO DE LA INTERFAZ WEB
# -------------------------------------------------------------
Write-Host "`n[6/6] Iniciando la suite Sadigua en http://localhost:7837..." -ForegroundColor Yellow
Start-Process "http://localhost:7837"
python sadigua.py web
