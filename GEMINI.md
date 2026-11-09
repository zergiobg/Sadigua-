# Reglas y Comandos del Proyecto Sadigua

## Comando Especial: "deploy Sadigua"
Cuando el usuario indique **"deploy Sadigua"**, **"monta Sadigua"** o **"instala Sadigua"**:
1. Activa y sigue rigurosamente el runbook definido en `.agents/skills/deploy-sadigua/SKILL.md`.
2. Alternativamente, ejecuta el script de automatización:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
   ```
3. Verifica que:
   - Python y los paquetes de `requirements.txt` estén listos.
   - El motor Ollama esté instalado y corriendo en segundo plano (`http://localhost:11434`).
   - El modelo local `qwen2.5:7b-instruct` esté descargado en la máquina.
   - El corpus inicial del cartucho activo esté indexado en BM25 y vectores.
   - Se inicie el servidor web de Sadigua en el puerto **`7837`** (`http://localhost:7837`).

## Principios Inmutables de Sadigua
- **Soberanía y Privacidad**: Por defecto la salida a nubes de terceros está estrictamente bloqueada (`CLOUD_EGRESS_ENABLED=False`).
- **Paleta Visual**: Interfaz web en azul, gris y blanco (cero modo oscuro).
- **Puerto de Red**: Siempre `7837`.
