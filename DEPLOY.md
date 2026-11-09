# GUÍA MAESTRA DE DESPLIEGUE AUTOMATIZADO: "deploy Sadigua"
## Puesta en marcha desatendida del Cerebro Soberano Sadigua en cualquier máquina

---

## ⚡ Método 1: Despliegue con Antigravity (1 Solo Comando de Voz o Chat)

Si estás utilizando **Antigravity** o cualquier agente compatible con el estándar de habilidades `.agents/`:

Simplemente escribe en el chat:
> **`deploy Sadigua`**

El agente detectará la regla en [`GEMINI.md`](./GEMINI.md) y la habilidad en [`.agents/skills/deploy-sadigua/SKILL.md`](./.agents/skills/deploy-sadigua/SKILL.md), y ejecutará de forma automática y desatendida los 6 pasos de instalación, auto-calibración de hardware, descarga de modelo e inicio de la interfaz web.

---

## 🖥️ Método 2: Despliegue Automatizado por Script (PowerShell)

En cualquier equipo Windows nuevo (despacho, universidad o servidor local):

1. Clona el repositorio:
   ```powershell
   git clone https://github.com/zergiobg/Sadigua-.git C:\Sadigua
   cd C:\Sadigua
   ```
2. Ejecuta el script de aprovisionamiento inteligente:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
   ```

El script se encargará de:
- Instalar dependencias Python.
- Instalar e iniciar el motor Ollama en segundo plano.
- Perfilar la CPU y memoria RAM para seleccionar y descargar automáticamente el modelo Qwen 2.5 correspondiente.
- Indexar el corpus normativo y las notas de la Bóveda Obsidian.
- Lanzar el servidor web en el puerto **`7837`** y abrir tu navegador en **`http://localhost:7837`**.

---

## 📋 Método 3: Paso a Paso Manual

Para entornos de consola o servidores Linux/Mac:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Iniciar Ollama
ollama serve

# 3. Descargar el modelo cuantizado
ollama pull qwen2.5:7b-instruct
# (En servidores con > 32 GB RAM):
# ollama pull qwen2.5:14b-instruct

# 4. Re-indexar el corpus
python sadigua.py ingest

# 5. Iniciar la suite
python sadigua.py web
```

---

## 💾 Método 4: Kit USB Portable (100% Offline con Modelos LLM Incluidos)

Si deseas llevar Sadigua en una memoria USB o disco duro externo a un cliente, juzgado o servidor sin conexión a internet:

### Cómo preparar tu memoria USB (desde tu equipo actual):
1. Conecta tu memoria USB (se recomienda al menos 8 GB libres).
2. Haz doble clic en [`PREPARAR_USB.bat`](./PREPARAR_USB.bat) o ejecuta:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\export_to_usb.ps1 -UsbDriveLetter E
   ```
   Esto copiará el código de Sadigua, los binarios de Ollama y los **4.7 GB del modelo Qwen 2.5** a la memoria USB.

### Cómo instalarlo en el computador nuevo:
1. Conecta la USB en el nuevo computador.
2. Abre la USB y haz doble clic en **`INSTALAR_SADIGUA.bat`**.
   - El instalador creará la carpeta (por defecto `C:\Sadigua`).
   - Transferirá el modelo Qwen 2.5 a la caché local del nuevo equipo en ~30 segundos (**cero descargas de internet**).
3. Abre **Antigravity** en `C:\Sadigua` y escribe en el chat:
   > **`deploy Sadigua`**
4. ¡Listo! El agente encenderá el motor y abrirá la suite en **`http://localhost:7837`**.
