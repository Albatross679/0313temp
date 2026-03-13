"""System & GPU metrics collection for per-epoch logging."""

from __future__ import annotations

import os
import platform
from typing import Optional

import torch


def collect_system_metrics(device: Optional[str] = None) -> dict[str, float]:
    """Gather GPU and system metrics, returning a flat dict ready for logging.

    Gracefully degrades: missing ``pynvml`` or ``psutil`` simply omit those
    metrics rather than raising.
    """
    metrics: dict[str, float] = {}

    # ── GPU memory (torch.cuda) ──────────────────────────────────────────
    if device and "cuda" in str(device) and torch.cuda.is_available():
        dev_idx = torch.cuda.current_device()
        metrics["gpu_mem_allocated_mb"] = torch.cuda.memory_allocated(dev_idx) / 1e6
        metrics["gpu_mem_reserved_mb"] = torch.cuda.memory_reserved(dev_idx) / 1e6
        metrics["gpu_mem_peak_mb"] = torch.cuda.max_memory_allocated(dev_idx) / 1e6

    # ── GPU utilization / temp / power (pynvml) ──────────────────────────
    try:
        import pynvml

        pynvml.nvmlInit()
        dev_idx = int(str(device).replace("cuda:", "").replace("cuda", "0"))
        handle = pynvml.nvmlDeviceGetHandleByIndex(dev_idx)

        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        metrics["gpu_util_pct"] = float(util.gpu)

        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        metrics["gpu_temp_c"] = float(temp)

        power = pynvml.nvmlDeviceGetPowerUsage(handle)  # milliwatts
        metrics["gpu_power_w"] = power / 1000.0

        pynvml.nvmlShutdown()
    except Exception:
        pass

    # ── CPU / RAM (psutil) ───────────────────────────────────────────────
    try:
        import psutil

        vm = psutil.virtual_memory()
        metrics["ram_used_gb"] = vm.used / 1e9
        metrics["ram_pct"] = vm.percent

        proc = psutil.Process(os.getpid())
        metrics["process_rss_mb"] = proc.memory_info().rss / 1e6

        metrics["cpu_pct"] = psutil.cpu_percent(interval=None)
    except Exception:
        pass

    return metrics


def collect_hardware_info() -> dict[str, str]:
    """Collect static hardware info (CPU, RAM, GPU, OS, etc.) for run logging.

    Called once at the start of a training run. All values are strings suitable
    for ``wandb.config.update``.
    """
    info: dict[str, str] = {}

    # ── OS / platform ─────────────────────────────────────────────────────
    info["os"] = f"{platform.system()} {platform.release()}"
    info["python_version"] = platform.python_version()

    # ── CPU ────────────────────────────────────────────────────────────────
    info["cpu_model"] = platform.processor() or "unknown"
    try:
        info["cpu_cores_physical"] = str(os.cpu_count())
    except Exception:
        pass
    try:
        import psutil
        info["cpu_cores_physical"] = str(psutil.cpu_count(logical=False))
        info["cpu_cores_logical"] = str(psutil.cpu_count(logical=True))
    except Exception:
        pass

    # ── RAM ────────────────────────────────────────────────────────────────
    try:
        import psutil
        total_gb = round(psutil.virtual_memory().total / 1e9, 1)
        info["ram_total_gb"] = str(total_gb)
    except Exception:
        pass

    # ── GPU ────────────────────────────────────────────────────────────────
    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name()
        info["cuda_version"] = torch.version.cuda or "unknown"
        info["cudnn_version"] = str(torch.backends.cudnn.version()) if torch.backends.cudnn.is_available() else "N/A"
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(torch.cuda.current_device())
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            info["gpu_mem_total_mb"] = str(round(mem.total / 1e6))
            driver = pynvml.nvmlSystemGetDriverVersion()
            info["gpu_driver_version"] = driver.decode() if isinstance(driver, bytes) else str(driver)
            pynvml.nvmlShutdown()
        except Exception:
            pass
    else:
        info["gpu_name"] = "N/A (CPU only)"

    # ── PyTorch ────────────────────────────────────────────────────────────
    info["torch_version"] = torch.__version__

    return info
