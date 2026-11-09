---
name: deploy-sadigua
description: >-
  Use this skill whenever the user instructs "deploy Sadigua", "instalar Sadigua",
  "montar Sadigua" or wants to automatically setup, install dependencies, configure hardware,
  download local Qwen LLM weights and launch the Sadigua Sovereign AI Brain on a new machine or server.
---

# Runbook: Despliegue Automatizado de SADIGUA ("deploy Sadigua")

Este runbook instruye a Antigravity (o a cualquier agente de IA) para ejecutar la instalación, verificación de hardware, aprovisionamiento del modelo local y puesta en marcha de la suite Sadigua de forma 100% desatendida.

---

## Protocolo de Ejecución Paso a Paso

Cuando el usuario dé la orden **"deploy Sadigua"**, ejecuta en orden estricto los siguientes pasos utilizando la terminal PowerShell:

### Paso 1: Verificación de Entorno Python y Dependencias
Verifica la presencia de Python (>= 3.10) e instala las dependencias necesarias:
```powershell
python --version
pip install -r requirements.txt
```

### Paso 2: Verificación e Instalación de Ollama (Motor Local)
Comprueba si Ollama está disponible en el sistema. Si no está instalado, ejecútalo vía `winget`:
```powershell
if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue) -and -not (Test-Path "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe")) {
    Write-Host "[*] Instalando Ollama para Windows..."
    winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements
}
```

### Paso 3: Encendido del Servicio Ollama en Segundo Plano
Asegúrate de que el daemon de Ollama esté escuchando en `http://localhost:11434`:
```powershell
$ollamaRunning = Get-Process -Name "*ollama*" -ErrorAction SilentlyContinue
if (-not $ollamaRunning) {
    Write-Host "[*] Iniciando servicio Ollama en segundo plano..."
    if (Get-Command "ollama" -ErrorAction SilentlyContinue) {
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    } else {
        Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" -ArgumentList "serve" -WindowStyle Hidden
    }
    Start-Sleep -Seconds 4
}
```

### Paso 4: Diagnóstico de Hardware y Selección de Modelo
Ejecuta el detector de hardware de Sadigua para calibrar la memoria RAM y procesador presentes:
```powershell
python -c "from core.hardware.detector import HardwareProfiler; print(HardwareProfiler.profile())"
```
Según el perfil retornado:
- Si la RAM es $\ge 24\text{ GB}$: Descarga `qwen2.5:14b-instruct` o `qwen2.5:7b-instruct`.
- Si la RAM es $< 24\text{ GB}$: Descarga `qwen2.5:7b-instruct` o `qwen2.5:3b-instruct`.

Comando de descarga del modelo:
```powershell
# En máquinas con >= 12 GB RAM (recomendado estándar):
ollama pull qwen2.5:7b-instruct
```

### Paso 5: Auto-Ingesta y Verificación de la Bóveda RAG
Ejecuta la re-indexación inicial del cartucho normativo:
```powershell
python sadigua.py ingest
```

### Paso 6: Lanzamiento de la Suite Sadigua
Inicia el servidor Web y el Gateway en el puerto 7837:
```powershell
Write-Host "[✓] Despliegue de Sadigua finalizado con éxito."
Write-Host "[*] Iniciando interfaz web en http://localhost:7837..."
python sadigua.py web
```

---

## Verificación Final del Despliegue
El agente debe confirmar al usuario:
1. URL activa: `http://localhost:7837`
2. Estado de Soberanía: 100% Local (Nube Bloqueada).
3. Modelo en memoria RAM: Qwen 2.5 local calibrado para los núcleos de la máquina.
4. Bóveda Obsidian activa en `vault/`.
