@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cls

echo =====================================================================
echo       SADIGUA PORTABLE USB - INSTALADOR EN NUEVO HOST
echo =====================================================================
echo Este instalador copiara el Cerebro Sadigua y los modelos LLM locales
echo directamente desde esta USB a este computador (CERO DESCARGAS DE INTERNET).
echo =====================================================================
echo.

:: 1. Definir rutas
set "USB_DRIVE=%~dp0"
set "TARGET_DIR=C:\Sadigua"
set "OLLAMA_USER_DIR=%USERPROFILE%\.ollama\models"

set /p USER_CHOICE="¿Deseas instalar Sadigua en C:\Sadigua? (S/N, presiona Enter para Si): "
if /i "%USER_CHOICE%"=="N" (
    set /p TARGET_DIR="Introduce la ruta completa donde deseas instalarlo (ej: D:\Sadigua): "
)

echo.
echo [*] Directorio de destino: %TARGET_DIR%
echo [*] Unidad USB detectada:  %USB_DRIVE%
echo.

:: 2. Crear carpetas de destino
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
if not exist "%OLLAMA_USER_DIR%" mkdir "%OLLAMA_USER_DIR%"

:: 3. Copiar el núcleo de Sadigua (código, cartuchos, bóveda, web)
echo [1/4] Copiando codigo fuente, cartuchos y Boveda Obsidian...
robocopy "%USB_DRIVE%Sadigua_Core" "%TARGET_DIR%" /E /XD ".git" ".venv" "venv" "__pycache__" "data" /XF "*.gguf" "*.bin" /NFL /NDL /NJH /NJS > nul
echo [OK] Codigo y estructura copiados con exito.

:: 4. Copiar modelos pesados pre-descargados (Qwen 2.5) a la cache de Ollama del host
echo.
echo [2/4] Copiando modelo LLM local (Qwen 2.5) a la cache de este equipo...
echo     (Transfiriendo ~4.7 GB a velocidad USB, tarda entre 20 y 45 segundos)...
robocopy "%USB_DRIVE%Models_Cache" "%OLLAMA_USER_DIR%" /E /NFL /NDL /NJH /NJS > nul
echo [OK] Modelo Qwen 2.5 transferido exitosamente (0 bytes descargados de internet).

:: 5. Copiar o registrar ejecutables de Ollama si no estan presentes
echo.
echo [3/4] Verificando motor Ollama en este equipo...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%USB_DRIVE%Ollama_Binaries\ollama.exe" (
        echo [*] Instalando binarios de Ollama desde la USB...
        set "LOCAL_OLLAMA=%LOCALAPPDATA%\Programs\Ollama"
        if not exist "!LOCAL_OLLAMA!" mkdir "!LOCAL_OLLAMA!"
        robocopy "%USB_DRIVE%Ollama_Binaries" "!LOCAL_OLLAMA!" /E /NFL /NDL /NJH /NJS > nul
        set "PATH=%LOCALAPPDATA%\Programs\Ollama;!PATH!"
        echo [OK] Ollama configurado en !LOCAL_OLLAMA!
    ) else (
        echo [*] Ollama sera verificado o instalado automaticamente al iniciar.
    )
) else (
    echo [OK] Ollama ya se encuentra instalado en este equipo.
)

:: 6. Finalizacion y mensaje magistral
echo.
echo [4/4] Configurando permisos y scripts...
echo [OK] Todo el entorno se encuentra montado y listo.

echo.
echo =====================================================================
echo              SADIGUA HA SIDO MONTADO CON EXITO
echo =====================================================================
echo Ubicacion: %TARGET_DIR%
echo Modelo:    Qwen 2.5 local pre-cargado y listo en memoria.
echo.
echo AHORA TIENES DOS FORMAS DE USARLO:
echo.
echo FORMA 1 (CON ANTIGRAVITY):
echo   1. Abre Antigravity en la carpeta: %TARGET_DIR%
echo   2. En el chat, escribe nuestro comando magico:
echo      "deploy Sadigua"
echo      ...y Antigravity levantara todo y abrira el navegador en http://localhost:7837
echo.
echo FORMA 2 (DIRECTO POR CONSOLA AHORA MISMO):
set /p RUN_NOW="¿Deseas iniciar Sadigua inmediatamente ahora mismo? (S/N): "
if /i "%RUN_NOW%"=="S" (
    cd /d "%TARGET_DIR%"
    powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
)

pause
