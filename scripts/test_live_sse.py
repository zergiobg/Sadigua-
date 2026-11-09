import httpx
import json
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "http://localhost:7837/api/chat/progressive"
payload = {"message": "¿Qué puedo hacer si una empresa vendió mis datos personales sin mi autorización?"}

print("=== ENVIANDO CONSULTA JURÍDICA AL ENDPOINT SSE ===", flush=True)
start = time.time()

with httpx.Client(timeout=60.0) as client:
    with client.stream("POST", url, json=payload) as response:
        token_count = 0
        current_wave = None
        for line in response.iter_lines():
            if not line:
                continue
            trimmed = line.strip()
            if not trimmed.startswith("data:"):
                continue
            data_str = trimmed[5:].strip()
            if not data_str:
                continue
            
            event = json.loads(data_str)
            evt_type = event.get("type")

            if evt_type == "phase":
                elapsed = time.time() - start
                print(f"[{elapsed:05.2f}s] FASE: {event.get('phase')} -> {event.get('message')}", flush=True)
            elif evt_type == "documents_found":
                print(f"[{time.time()-start:05.2f}s] DOCUMENTOS IDENTIFICADOS:", flush=True)
                for d in event.get("documents", []):
                    lbl = d.get('articulo') or d.get('section')
                    print(f"   * {d.get('source')} | {lbl} (Score: {d.get('score')})", flush=True)
            elif evt_type == "token":
                wave = event.get("wave")
                if wave != current_wave:
                    current_wave = wave
                    print(f"\n--- INICIO DE ONDA {current_wave} (STREAMING DE TOKENS) ---", flush=True)
                token_count += 1
                if token_count <= 5 or token_count % 25 == 0:
                    print(f"[{time.time()-start:05.2f}s] Token #{token_count}: '{event.get('text', '').strip()}'", flush=True)
            elif evt_type == "precedent_hit":
                print(f"\n⚡ PRECEDENTE INSTANTÁNEO EN BÓVEDA (Match: {event.get('similarity')*100:.1f}%)", flush=True)
                print(f"   Nota ID: {event.get('note_id')}", flush=True)
                print(f"   Respuesta: {event.get('answer', '')[:120]}...", flush=True)
                break
            elif evt_type == "grounding":
                print(f"\n[{time.time()-start:05.2f}s] GROUNDING VALIDADO: {event.get('grounding_status')}", flush=True)
                print(f"   Citas encontradas: {event.get('citations')}", flush=True)
            elif evt_type == "done":
                print(f"[{time.time()-start:05.2f}s] PROCESO FINALIZADO. Total tokens: {token_count}", flush=True)
                break
