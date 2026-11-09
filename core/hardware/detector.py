import os
import platform
import psutil
from typing import Dict, Any

class HardwareProfiler:
    """
    Motor de Detección de Hardware y Auto-Reconfiguración Dinámica de Sadigua.
    Permite que el sistema se transporte a cualquier máquina (laptop modesta, servidor o estación de trabajo)
    y calibre automáticamente los hilos de CPU, ventana de contexto y tamaño de modelo recomendado.
    """

    @classmethod
    def profile(cls) -> Dict[str, Any]:
        # 1. CPU
        logical_cores = psutil.cpu_count(logical=True) or os.cpu_count() or 4
        physical_cores = psutil.cpu_count(logical=False) or max(1, logical_cores // 2)

        # Asignar hilos óptimos para procesadores híbridos Intel (P-cores + E-cores)
        # En procesadores con 12+ hilos (como Intel Core Ultra), 8 hilos maximiza la velocidad
        # evitando la latencia de sincronización de los núcleos LP-E del SoC.
        if logical_cores >= 12:
            optimal_threads = 8
        elif logical_cores > 4:
            optimal_threads = max(2, logical_cores - 2)
        else:
            optimal_threads = max(1, logical_cores - 1)

        # 2. Memoria RAM
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024 ** 3), 2)
        ram_available_gb = round(mem.available / (1024 ** 3), 2)

        # 3. Detección de GPU (CUDA / Apple Silicon / CPU)
        has_cuda = False
        gpu_name = "No dedicada (Inferencia optimizada en CPU AVX2/VNNI)"
        try:
            import subprocess
            smi = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True)
            if smi.returncode == 0 and smi.stdout.strip():
                has_cuda = True
                gpu_name = smi.stdout.strip()
        except Exception:
            pass

        # 4. Dimensionamiento y Recomendación Automática de Modelo
        # Qwen 2.5 familias: 1.5B (~1.2 GB), 3B (~2.5 GB), 7B (~4.7 GB), 14B (~9.5 GB), 32B (~20 GB)
        if ram_total_gb >= 48:
            recommended_model = "qwen2.5:14b-instruct"
            max_recommended_model = "qwen2.5:32b-instruct"
            recommended_ctx = 8192
            tier = "Enterprise Workstation / Alta Capacidad"
        elif ram_total_gb >= 24:
            recommended_model = "qwen2.5:14b-instruct"
            max_recommended_model = "qwen2.5:14b-instruct"
            recommended_ctx = 4096
            tier = "Pro Laptop / Capacidad Alta (Tu Máquina Actual)"
        elif ram_total_gb >= 12:
            recommended_model = "qwen2.5:7b-instruct"
            max_recommended_model = "qwen2.5:7b-instruct"
            recommended_ctx = 4096
            tier = "Laptop Estándar / Capacidad Media"
        elif ram_total_gb >= 6:
            recommended_model = "qwen2.5:3b-instruct"
            max_recommended_model = "qwen2.5:3b-instruct"
            recommended_ctx = 2048
            tier = "Hardware Modesto / Ultraportátil"
        else:
            recommended_model = "qwen2.5:1.5b-instruct"
            max_recommended_model = "qwen2.5:1.5b-instruct"
            recommended_ctx = 2048
            tier = "Hardware Mínimo / Edge IoT"

        return {
            "platform": platform.platform(),
            "cpu_architecture": platform.machine(),
            "processor": platform.processor(),
            "physical_cores": physical_cores,
            "logical_cores": logical_cores,
            "optimal_threads": optimal_threads,
            "ram_total_gb": ram_total_gb,
            "ram_available_gb": ram_available_gb,
            "has_cuda": has_cuda,
            "gpu_name": gpu_name,
            "hardware_tier": tier,
            "recommendations": {
                "active_model": recommended_model,
                "max_capable_model": max_recommended_model,
                "context_window_tokens": recommended_ctx,
                "recommended_num_threads": optimal_threads
            }
        }
