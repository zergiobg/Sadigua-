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

La suite abrirá de inmediato en **`http://localhost:7837`** de forma 100% autónoma y sin conexión a internet.
