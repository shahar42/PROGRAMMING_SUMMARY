# Model Loading Optimization Log

## Date: 2025-10-14

## Problem
Loading a fine-tuned Llama 3.1 8B model was freezing the system during startup.

## Root Cause Analysis
We diagnosed a critical memory issue where loading a fine-tuned Llama 3.1 8B model was freezing your system. The root cause was attempting to load a 30GB model (in float32) on a system with only 14GB RAM, compounded by the `merge_and_unload()` operation that temporarily doubled memory usage.

## Investigation Steps
We identified your 1.8TB external drive (sdc1) and successfully mounted it at `/mnt/external`, locating your trained model at `/mnt/external/models/cpp-instructor/`. After consulting Perplexity AI for best practices, we determined that 4-bit quantization without merging was the optimal solution, reducing memory requirements from ~30GB to under 10GB.

## Solution Implemented
We installed the required packages: `bitsandbytes` for quantization and `peft` for efficient model loading. We created a new optimized script (`cpp_instructor_quantized.py`) that uses 4-bit quantization via BitsAndBytesConfig, eliminating the problematic merge operation. The new script includes proper device mapping with `device_map="auto"` for efficient memory management. It also features memory monitoring capabilities and an improved CLI interface with interactive and single-question modes.

## Results
The solution addresses the external drive I/O bottleneck by using low_cpu_mem_usage=True and streaming model loading. Your system should now stay responsive during model loading, with the initial load taking 2-5 minutes from the external drive but without freezing.

## Key Changes
- **Memory reduction**: 30GB → <10GB (4-bit quantization)
- **No model merging**: Eliminated `merge_and_unload()` operation
- **Efficient device mapping**: Using `device_map="auto"`
- **New script**: `cpp_instructor_quantized.py`

## Usage
```bash
# Interactive mode
python cpp_instructor_quantized.py

# Single question
python cpp_instructor_quantized.py --question "Explain smart pointers"
```
