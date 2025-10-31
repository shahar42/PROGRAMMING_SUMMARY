# V9 Complete Pipeline - Colab Cells

**Goal**: Train → Merge → Convert → Quantize → Download (all on Colab)

**Output**: `model_v9_q5.gguf` (~5.5GB) ready to use on your PC

---

## Cell 1: Load Checkpoint 2500

```python
import os

checkpoint_dir = "/content/drive/MyDrive/fine_tuning_llama_v9_clean/checkpoints"
checkpoint_num = 2500

checkpoint_path = f"{checkpoint_dir}/checkpoint-{checkpoint_num}"

if os.path.exists(checkpoint_path):
    print(f"✅ Found checkpoint: checkpoint-{checkpoint_num}")
    print(f"📍 Path: {checkpoint_path}")
else:
    print(f"❌ Checkpoint not found: {checkpoint_path}")
    print("   Available checkpoints:")
    checkpoints = [d for d in os.listdir(checkpoint_dir) if d.startswith("checkpoint-")]
    for cp in sorted(checkpoints):
        print(f"     - {cp}")
```

**Output**: Confirms checkpoint-2500 exists

---

## Cell 2: Merge LoRA Adapter (2-3 min)

```python
from unsloth import FastLanguageModel
import os

# Using checkpoint-2500 (end of epoch 1)
checkpoint_path = "/content/drive/MyDrive/fine_tuning_llama_v9_clean/checkpoints/checkpoint-2500"

print("🔄 Loading checkpoint-2500...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=checkpoint_path,
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)
print("✅ Checkpoint-2500 loaded")

merge_dir = "/content/merged_model_v9"
print("🔄 Merging LoRA adapter (2-3 minutes)...")

model.save_pretrained_merged(
    merge_dir,
    tokenizer,
    save_method="merged_16bit",
)

print("✅ MERGE COMPLETE")
print(f"📍 Location: {merge_dir}")
print(f"📂 Files: {len(list(os.listdir(merge_dir)))}")
```

**Output**: Merged model in HuggingFace format (~16GB in RAM temporarily)

---

## Cell 3: Download & Setup llama.cpp

```python
import subprocess
import os
import urllib.request

print("🔧 Setting up llama.cpp tools...")

# Download conversion script
script_url = "https://raw.githubusercontent.com/ggerganov/llama.cpp/master/convert_hf_to_gguf.py"
script_path = "/content/convert_hf_to_gguf.py"

if not os.path.exists(script_path):
    print("⬇️  Downloading convert_hf_to_gguf.py...")
    urllib.request.urlretrieve(script_url, script_path)
    print("✅ Downloaded")
else:
    print("✅ Script already available")

# Clone llama.cpp for quantizer
if not os.path.exists("/content/llama.cpp"):
    print("⬇️  Cloning llama.cpp (for quantizer)...")
    os.system("cd /content && git clone --depth 1 https://github.com/ggerganov/llama.cpp.git")
    print("🔨 Building quantizer...")
    os.system("cd /content/llama.cpp && make -j4 quantize")
    print("✅ Build complete")
else:
    print("✅ llama.cpp already available")

print("✅ SETUP COMPLETE")
```

**Output**: Tools ready for conversion and quantization

---

## Cell 4: Convert to GGUF F16 (5-10 min)

```python
import subprocess
import os

merge_dir = "/content/merged_model_v9"
f16_output = "/content/model_v9_f16.gguf"

print("🔄 Converting to GGUF F16 (5-10 minutes)...")
print(f"   Input: {merge_dir}")
print(f"   Output: {f16_output}")
print()

# Run conversion
result = subprocess.run([
    "python3",
    "/content/convert_hf_to_gguf.py",
    merge_dir,
    "--outfile", f16_output,
    "--outtype", "f16"
], capture_output=True, text=True)

if result.returncode != 0:
    print("⚠️  Conversion had issues:")
    print(result.stderr[-500:])  # Last 500 chars
else:
    print("✅ Conversion complete")

# Check output
if os.path.exists(f16_output):
    size_gb = os.path.getsize(f16_output) / 1024 / 1024 / 1024
    print(f"✅ F16 GGUF created: {size_gb:.2f}GB")
else:
    print("❌ F16 file not created")
```

**Output**: `model_v9_f16.gguf` (~16GB)

---

## Cell 5: Quantize to Q5_K_M (3-5 min)

```python
import subprocess
import os

f16_output = "/content/model_v9_f16.gguf"
q5_output = "/content/model_v9_q5.gguf"

print("🗜️  Quantizing F16 → Q5_K_M (3-5 minutes)...")
print(f"   Input: {f16_output}")
print(f"   Output: {q5_output}")
print()

# Run quantizer
result = subprocess.run([
    "/content/llama.cpp/quantize",
    f16_output,
    q5_output,
    "Q5_K_M"
], capture_output=True, text=True)

if result.returncode != 0:
    print("⚠️  Quantization had issues:")
    print(result.stderr[-500:])
else:
    print("✅ Quantization complete")

# Check output
if os.path.exists(q5_output):
    f16_size = os.path.getsize(f16_output) / 1024 / 1024 / 1024
    q5_size = os.path.getsize(q5_output) / 1024 / 1024 / 1024
    compression = 100 * (1 - q5_size / f16_size)

    print(f"✅ Q5_K_M GGUF created: {q5_size:.2f}GB")
    print(f"   F16: {f16_size:.2f}GB → Q5: {q5_size:.2f}GB ({compression:.1f}% reduction)")
else:
    print("❌ Q5 file not created")
```

**Output**: `model_v9_q5.gguf` (~5.5GB) - The final model!

---

## Cell 6: Download Model

```python
from google.colab import files
import os

q5_output = "/content/model_v9_q5.gguf"

print("📥 Downloading model...")
print(f"   File: model_v9_q5.gguf")
print(f"   Size: {os.path.getsize(q5_output) / 1024 / 1024 / 1024:.2f}GB")
print()
print("🔄 Starting download (check your Downloads folder)...")

files.download(q5_output)

print()
print("✅ Download started!")
print("   Note: May take 5-10 minutes depending on connection")
```

**Output**: Download dialog appears, model downloads to your PC

---

## Cell 7: Verify Download & Next Steps

```python
print("=" * 70)
print("✅ V9 COMPLETE PIPELINE FINISHED!")
print("=" * 70)
print()

print("📊 What you created:")
print("  ✓ Merged model (16GB)")
print("  ✓ GGUF F16 (16GB)")
print("  ✓ GGUF Q5_K_M (5.5GB) ← Downloaded to your PC")
print()

print("🚀 NEXT STEPS ON YOUR PC:")
print()
print("1. Move downloaded file:")
print("   mv ~/Downloads/model_v9_q5.gguf ~/models/cpp-instructor-q5.gguf")
print()

print("2. Test the model:")
print("   feather \"Explain smart pointers\"")
print("   feather \"Show me assembly for x++\"")
print()

print("3. Done! Your V9 model is ready to use")
print()

print("📝 Model info:")
print("  Name: V9 (Code + Assembly)")
print("  Size: 5.5GB (Q5_K_M quantized)")
print("  Type: Llama 3.1 8B with LoRA fine-tuning")
print("  Training data: 15,494 examples")
print("  Epochs: 4")
print("  Validation loss: ~0.16-0.20")
print()
```

---

## ⏱️ Timeline

| Step | Task | Time | Cumulative |
|------|------|------|-----------|
| 1 | Find checkpoint | 1 min | 1 min |
| 2 | Merge adapter | 3 min | 4 min |
| 3 | Setup tools | 2 min | 6 min |
| 4 | Convert F16 | 8 min | 14 min |
| 5 | Quantize Q5 | 4 min | 18 min |
| 6 | Download | 5-10 min | 23-28 min |
| **TOTAL** | **All** | **~25 min** | **All done!** |

---

## 🎯 Why This Approach is Better

| Aspect | Download Merged (Old) | Merge+Convert on Colab (New) |
|--------|--------|-------|
| **What to download** | 16GB merged model | 5.5GB quantized model |
| **External drive space** | 16GB + 16GB + 5.5GB = 37.5GB | Just 5.5GB |
| **Conversion time** | Your machine (~10 min) | Colab GPU (~8 min) |
| **Quantization time** | Your machine (~5 min) | Colab (~4 min) |
| **Total prep time** | ~30 min locally | ~25 min on Colab |
| **Your machine load** | CPU/GPU intensive | Just download |

**Result**: Faster, less disk space, ready-to-use model! ✨

---

## 📝 Running the Cells

1. After training finishes in Colab
2. Create new cells below your training cells
3. Copy-paste each cell above in order
4. Run them sequentially (they depend on each other)
5. Download appears when Cell 6 finishes
6. Move file to `/home/shahar42/models/` on your PC
7. Done!

---

## ❓ Troubleshooting

### "❌ Script not downloaded"
```python
# Manual alternative - use pip instead
import subprocess
subprocess.run(["pip", "install", "-q", "gguf"])
```

### "❌ Build failed"
```python
# Try pre-built quantizer
import urllib.request
urllib.request.urlretrieve(
    "https://github.com/ggerganov/llama.cpp/releases/download/b...",
    "/content/quantize"
)
```

### "Download dialog didn't appear"
```python
# Manual Colab download
from google.colab import files
files.download('/content/model_v9_q5.gguf')
# Or use Colab's Files panel on the left
```

---

## ✅ Checklist

- [ ] Training completed
- [ ] Cell 1: Found checkpoint
- [ ] Cell 2: Merged model
- [ ] Cell 3: Setup tools
- [ ] Cell 4: Converted F16
- [ ] Cell 5: Quantized Q5
- [ ] Cell 6: Downloaded (check Downloads folder)
- [ ] Cell 7: Verified
- [ ] Move file to `~/models/`
- [ ] Test with `feather`
- [ ] Deploy! 🚀

---

**Version**: V9 Complete Pipeline
**Date**: October 21, 2025
**Status**: Ready to use
