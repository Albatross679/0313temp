---
name: GPU Throughput Metrics
description: Explanation of GPU throughput indicators — iterations/s, SM occupancy, and memory bandwidth utilization
type: knowledge
created: 2026-03-12
updated: 2026-03-12
tags: [gpu, performance, profiling, training]
aliases: [gpu-metrics, throughput-indicators]
---

# GPU Throughput Metrics

GPU utilization percentage (as reported by `nvidia-smi`) is a coarse metric — it only
shows whether the GPU is doing *something*, not how efficiently. These three metrics give
a much clearer picture of actual throughput.

## Iterations per Second (it/s)

How many training batches the model processes per second. This is the most practical,
end-to-end measure of training speed. Visible in tqdm progress bars (e.g., `10it/s`).
Higher = faster training. Useful for comparing configurations (batch size, precision,
model size) on the same hardware.

## SM (Streaming Multiprocessor) Occupancy

A GPU is composed of many **Streaming Multiprocessors (SMs)**, each containing CUDA cores
that execute operations in parallel. Occupancy measures the percentage of SMs actively
running **warps** (groups of 32 threads) at any given time.

- **Low occupancy** (e.g., 30%) means most compute hardware is idle — often caused by
  small batch sizes, excessive kernel launch overhead, or poor parallelism.
- **High occupancy** (e.g., 80%+) means the GPU's compute units are well-utilized.

**How to measure:** NVIDIA Nsight Compute (`ncu`), `torch.profiler`, or
`torch.cuda.utilization()`.

## Memory Bandwidth Utilization

GPUs have a theoretical peak rate for moving data between VRAM and compute cores, measured
in GB/s. For example:

| GPU       | Peak Memory Bandwidth |
|-----------|-----------------------|
| V100      | ~900 GB/s             |
| A100      | ~2,039 GB/s           |
| H100      | ~3,350 GB/s           |

This metric measures how close actual data transfer is to that peak. Many operations —
element-wise ops, normalization, attention — are **memory-bound**: the bottleneck is data
movement, not arithmetic. If utilization is low (e.g., 40% of peak), improvements are
possible via:

- **Kernel fusion** (combining multiple small operations into one GPU kernel)
- **Mixed precision** (FP16/BF16 halves memory traffic)
- **Better data layouts** (contiguous memory access patterns)

## Summary

| Metric                     | What it tells you              | Bottleneck it reveals |
|----------------------------|--------------------------------|-----------------------|
| it/s                       | Overall training speed         | End-to-end throughput |
| SM occupancy               | Compute unit utilization       | Compute-bound issues  |
| Memory bandwidth utilization | Data transfer efficiency     | Memory-bound issues   |

**Rule of thumb:** it/s tells you *how fast* training runs. SM occupancy and memory
bandwidth tell you *why* — whether the bottleneck is compute or memory.
