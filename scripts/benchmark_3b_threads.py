import time
import httpx

def benchmark_3b_threads(threads_list=[4, 6, 8, 10, 12]):
    url = "http://localhost:11434/api/chat"
    prompt = "Explica en dos parrafos que es el debido proceso en el derecho colombiano."

    print("=" * 65)
    print(" BENCHMARK DE HILOS CPU - OLLAMA QWEN 2.5 3B INSTRUCT")
    print("=" * 65)

    results = []

    for t in threads_list:
        payload = {
            "model": "qwen2.5:3b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "num_thread": t,
                "num_predict": 120,
                "temperature": 0.1
            },
            "keep_alive": "30m"
        }

        t0 = time.time()
        try:
            with httpx.Client(timeout=120) as client:
                resp = client.post(url, json=payload)
            t1 = time.time()

            d = resp.json()
            total_time = round(t1 - t0, 2)
            eval_count = d.get("eval_count", 0)
            eval_dur_s = (d.get("eval_duration", 1) / 1e9)
            tok_per_sec = round(eval_count / eval_dur_s, 2) if eval_dur_s > 0 else 0
            prompt_eval_dur_s = round(d.get("prompt_eval_duration", 0) / 1e9, 2)

            print(f"Hilos: {t:2d} | Total: {total_time:5.2f}s | Prefill: {prompt_eval_dur_s:4.2f}s | Gen: {eval_dur_s:5.2f}s | Vel: {tok_per_sec:5.2f} tok/s | Tokens: {eval_count}")
            results.append((t, total_time, tok_per_sec, prompt_eval_dur_s))
        except Exception as e:
            print(f"Error con {t} hilos: {e}")

    if results:
        print("=" * 65)
        best_tok = max(results, key=lambda x: x[2])
        best_time = min(results, key=lambda x: x[1])
        print(f"Mejor rendimiento 3B: {best_tok[0]} hilos con {best_tok[2]} tokens/segundo.")
        print(f"Menor tiempo total 3B: {best_time[0]} hilos con {best_time[1]} segundos.")
        print("=" * 65)
    return results

if __name__ == "__main__":
    benchmark_3b_threads([4, 6, 8, 10, 12])
