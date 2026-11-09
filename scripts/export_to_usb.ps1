# =====================================================================
# SADIGUA - CREADOR DE KIT USB PORTABLE (CON MODELOS LLM INCLUIDOS)
# =====================================================================

param (
    [string]$UsbDriveLetter = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "     SADIGUA - CREADOR DEL KIT USB PORTABLE CON LLM LOCAL        " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Identificar unidad USB
if (-not $UsbDriveLetter) {
    # Listar unidades removibles o discos externos
    $drives = Get-Volume | Where-Object { $_.DriveType -eq 'Removable' -or $_.FileSystemLabel -like '*USB*' }
    if ($drives) {
        Write-Host "`nUnidades USB detectadas:" -ForegroundColor Yellow
        $drives | Format-Table DriveLetter, FriendlyName, FileSystemLabel, @{Name="FreeGB"; Expression={[math]::Round($_.SizeRemaining/1GB, 1)}}, @{Name="TotalGB"; Expression={[math]::Round($_.Size/1GB, 1)}} -AutoSize
    }

    $UsbDriveLetter = Read-Host "`nIntroduce la letra de la unidad USB (ej: E, F, D)"
}

$UsbDriveLetter = $UsbDriveLetter.TrimEnd(":").Trim() + ":"
$usbRoot = "$UsbDriveLetter\"

if (-not (Test-Path $usbRoot)) {
    Write-Host "[!] Error: La unidad '$usbRoot' no existe o no esta conectada." -ForegroundColor Red
    exit 1
}

$freeSpaceGB = [math]::Round((Get-PSDrive ($UsbDriveLetter.TrimEnd(":"))).Free / 1GB, 2)
Write-Host "[*] Unidad USB seleccionada: $usbRoot (Espacio disponible: $freeSpaceGB GB)" -ForegroundColor Green

if ($freeSpaceGB -lt 6.0) {
    Write-Host "[!] Advertencia: Se recomiendan al menos 6 GB libres para copiar el modelo LLM completo (4.7 GB) y el sistema." -ForegroundColor Yellow
}

$baseDir = Split-Path -Parent $PSScriptRoot

# -------------------------------------------------------------
# PASO 1: COPIAR NÚCLEO DE SADIGUA A LA USB
# -------------------------------------------------------------
$destCore = Join-Path $usbRoot "Sadigua_Core"
Write-Host "`n[1/4] Copiando codigo fuente, frontend, cartuchos y Boveda Obsidian..." -ForegroundColor Cyan
robocopy $baseDir $destCore /E /XD ".git" ".venv" "venv" "__pycache__" "data" /XF ".env" "*.gguf" "*.bin" /NFL /NDL /NJH /NJS | Out-Null
Write-Host "[OK] Codigo fuente copiado en '$destCore' (< 1 MB)." -ForegroundColor Green

# -------------------------------------------------------------
# PASO 2: COPIAR CACHE DE MODELOS LLM (QWEN 2.5 4.7 GB)
# -------------------------------------------------------------
$ollamaModelsSource = "$env:USERPROFILE\.ollama\models"
$destModels = Join-Path $usbRoot "Models_Cache"

if (Test-Path $ollamaModelsSource) {
    Write-Host "`n[2/4] Copiando modelo Qwen 2.5 local (pesos matematicos)..." -ForegroundColor Cyan
    Write-Host "     (Transfiriendo ~4.7 GB a la USB, esto puede tomar entre 1 y 3 minutos segun la velocidad de tu pendrive)..." -ForegroundColor Gray
    robocopy $ollamaModelsSource $destModels /E /NFL /NDL /NJH /NJS | Out-Null
    Write-Host "[OK] Modelos LLM copiados exitosamente en '$destModels'." -ForegroundColor Green
} else {
    Write-Host "[!] No se detecto la carpeta de modelos en '$ollamaModelsSource'." -ForegroundColor Yellow
}

# -------------------------------------------------------------
# PASO 3: COPIAR BINARIOS DE OLLAMA
# -------------------------------------------------------------
$ollamaBinSource = "$env:LOCALAPPDATA\Programs\Ollama"
$destBin = Join-Path $usbRoot "Ollama_Binaries"

if (Test-Path $ollamaBinSource) {
    Write-Host "`n[3/4] Copiando binarios ejecutables de Ollama..." -ForegroundColor Cyan
    robocopy $ollamaBinSource $destBin /E /NFL /NDL /NJH /NJS | Out-Null
    Write-Host "[OK] Ejecutables de Ollama copiados en '$destBin'." -ForegroundColor Green
}

# -------------------------------------------------------------
# PASO 4: COPIAR EL INSTALADOR AUTOMÁTICO 'INSTALAR_SADIGUA.bat'
# -------------------------------------------------------------
$installerTemplate = Join-Path $baseDir "usb_template\INSTALAR_SADIGUA.bat"
$destInstaller = Join-Path $usbRoot "INSTALAR_SADIGUA.bat"

if (Test-Path $installerTemplate) {
    Copy-Item -Path $installerTemplate -Destination $destInstaller -Force
    Write-Host "`n[4/4] Instalador 'INSTALAR_SADIGUA.bat' colocado en la raiz de la USB." -ForegroundColor Green
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "         ¡KIT USB PORTABLE DE SADIGUA CREADO CON ÉXITO!          " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Tu USB ($usbRoot) ahora contiene:"
Write-Host " • INSTALAR_SADIGUA.bat   -> El lanzador en 1 clic para cualquier computador nuevo."
Write-Host " • Sadigua_Core\          -> El cerebro, frontend web, cartuchos y memoria Obsidian."
Write-Host " • Models_Cache\          -> El modelo Qwen 2.5 pre-descargado (4.7 GB)."
Write-Host " • Ollama_Binaries\       -> El motor de ejecucion local."
Write-Host "`nCuando conectes la USB en un computador nuevo:"
Write-Host " 1. Haz doble clic en 'INSTALAR_SADIGUA.bat'."
Write-Host " 2. Abre Antigravity en la carpeta creada (ej: C:\Sadigua)."
Write-Host " 3. Escribe nuestro comando magico: 'deploy Sadigua'."
Write-Host " ¡Y todo quedara montado y funcionando de inmediato!" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
