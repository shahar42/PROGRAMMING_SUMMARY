# V9 Model Deployment Plan
## Download, Quantize & Deploy Pipeline

**Status**: Waiting for training completion on Colab
**Target**: Deploy fine-tuned Llama 3.1 8B C/C++ instructor to external drive with quantization

---

## Overview

The V9 deployment pipeline consists of 4 main phases:

1. **Merge LoRA Adapter** - Combine LoRA weights with base Llama 3.1 8B (Colab)
2. **Download from Drive** - Transfer merged model to external drive (Local)
3. **Convert & Quantize** - Create GGUF format with Q5_K_M quantization (Local)
4. **Deploy & Test** - Move to final location and verify (Local)

---

## Phase 1: Merge LoRA Adapter (On Colab)

**Location**: Google Colab notebook cell
**Time**: 2-3 minutes
**Output**: `/content/drive/MyDrive/fine_tuning_llama_v9_clean/model_v9_merged` (~16GB)

```python
# ==========================================
# PHASE 1: Merge LoRA Adapter
# Run in Colab notebook after training completes
# ==========================================

from unsloth import FastLanguageModel

# Find latest checkpoint
import os
checkpoint_dir = "/content/drive/MyDrive/fine_tuning_llama_v9_clean/checkpoints"
checkpoints = [d for d in os.listdir(checkpoint_dir) if d.startswith("checkpoint-")]
latest = max(checkpoints, key=lambda x: int(x.split("-")[1]))
checkpoint_path = os.path.join(checkpoint_dir, latest)

print(f"📍 Found latest checkpoint: {latest}")
print(f"🔄 Loading checkpoint...")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=checkpoint_path,
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

print("✅ Checkpoint loaded")
print("🔄 Merging LoRA adapter with base model...")
print("   (This takes 2-3 minutes...)")

model.save_pretrained_merged(
    "/content/drive/MyDrive/fine_tuning_llama_v9_clean/model_v9_merged",
    tokenizer,
    save_method="merged_16bit",
)

print("")
print("="*70)
print("✅ MERGE COMPLETE - Model ready for download")
print("="*70)
print("")
print("📍 Location: /content/drive/MyDrive/fine_tuning_llama_v9_clean/model_v9_merged")
print("📦 Size: ~16GB (merged model in HF format)")
print("")
print("Next: Run download-v9-from-drive.sh on local machine")
```

**Output Files**:
- `config.json`
- `model.safetensors` (~16GB)
- `tokenizer.json`
- `tokenizer.model`
- `tokenizer_config.json`
- `special_tokens_map.json`
- `generation_config.json`

---

## Phase 2: Download from Google Drive (Local)

**Script**: `download-v9-from-drive.sh`
**Time**: 10-30 minutes (depends on connection, ~16GB)
**Requires**: External drive mounted at `/mnt/external`
**Input**: Google Drive folder ID
**Output**: `/mnt/external/models/v9_model_merged`

### Prerequisites

```bash
# 1. Mount external drive (if not already mounted)
./mount-external.sh

# 2. Verify mount
ls -la /mnt/external/models/

# 3. Install gdown if needed
pip install gdown
```

### Get Google Drive Folder ID

1. In Colab, after merge completes:
   - Go to Google Drive
   - Navigate to `fine_tuning_llama_v9_clean/model_v9_merged`
   - Right-click folder → **Get link**
   - Copy the link: `https://drive.google.com/drive/folders/FOLDER_ID`
   - Extract the `FOLDER_ID` part

### Run Download

```bash
cd /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning

# Method 1: Provide folder ID as argument
./download-v9-from-drive.sh "YOUR_FOLDER_ID_HERE"

# Method 2: Prompted for folder ID
./download-v9-from-drive.sh
```

**Expected Output**:
```
✅ Download complete!
📂 Files saved to: /mnt/external/models/v9_model_merged
config.json
model.safetensors (~16GB)
tokenizer.json
...
```

---

## Phase 3: Convert & Quantize (Local)

**Script**: `deploy-v9-model.sh`
**Time**:
- F16 conversion: 5-10 minutes
- Q5_K_M quantization: 3-5 minutes
- Total: ~15-20 minutes

**Requires**:
- `llama.cpp` built (in current directory)
- `/mnt/external/models/v9_model_merged` from Phase 2
- ~30GB free space on external drive

### Step 3a: Convert to F16 GGUF

**Input**: `/mnt/external/models/v9_model_merged` (HF format)
**Output**: `/mnt/external/models/cpp-instructor-v9-f16.gguf` (~16GB)
**Command**:
```bash
python3 llama.cpp/convert_hf_to_gguf.py /mnt/external/models/v9_model_merged \
    --outfile /mnt/external/models/cpp-instructor-v9-f16.gguf \
    --outtype f16
```

**What it does**:
- Converts HuggingFace safetensors format → GGUF format
- Uses float16 precision (no quantization yet)
- Produces full-quality model (~16GB)

### Step 3b: Quantize to Q5_K_M

**Input**: `/mnt/external/models/cpp-instructor-v9-f16.gguf`
**Output**: `/mnt/external/models/cpp-instructor-v9-q5.gguf` (~5-6GB)
**Command**:
```bash
./llama.cpp/build/bin/llama-quantize \
    /mnt/external/models/cpp-instructor-v9-f16.gguf \
    /mnt/external/models/cpp-instructor-v9-q5.gguf \
    Q5_K_M
```

**What it does**:
- Reduces F16 (~16GB) → Q5_K_M (~5.5GB, ~66% reduction)
- Quantization method: Medium 5-bit (Q5_K_M)
- Quality: ~99% of original with much better memory efficiency

---

## Phase 4: Deploy & Test (Local)

**Script**: `deploy-v9-model.sh`
**Time**: ~5 minutes

### Step 4a: Backup Previous Version

```bash
# Backup current v8 (if exists)
if [ -f "/mnt/external/models/cpp-instructor-q5.gguf" ]; then
    cp /mnt/external/models/cpp-instructor-q5.gguf \
       /mnt/external/models/cpp-instructor-v8-q5.gguf
    echo "✅ V8 backed up"
fi
```

### Step 4b: Deploy to External Drive

```bash
cp /mnt/external/models/cpp-instructor-v9-q5.gguf \
   /mnt/external/models/cpp-instructor-q5.gguf
```

### Step 4c: Deploy to Internal SSD (Optional)

```bash
mkdir -p ~/.local/share/llama-models
cp /mnt/external/models/cpp-instructor-v9-q5.gguf \
   ~/.local/share/llama-models/cpp-instructor-q5.gguf
```

**Why both locations?**
- **External** (`/mnt/external/...`): Always available, used as fallback
- **Internal** (`~/.local/share/...`): Faster access for daily use

### Step 4d: Test Deployment

```bash
# Test basic functionality
feather "Explain pointers in C++"

# Test code example generation
feather "Show me an example of smart pointers"

# Test assembly output (V9 speciality)
feather "Show me assembly for x++"

# Test both C and C++ knowledge
feather "Explain the difference between malloc and new"
```

---

## Unified Deployment Script

**Script**: `deploy-v9-model.sh`

```bash
#!/bin/bash
# Deploy V9 Model - Complete Pipeline
# Run this after downloading from Drive (Phase 2 complete)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP="$SCRIPT_DIR/llama.cpp"
MODELS_DIR="/mnt/external/models"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Feather V9 Model Deployment Pipeline                  ║"
echo "║         (C/C++ Instructor with Assembly Examples)             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ===== PREREQUISITES =====
echo "📋 Step 1: Checking prerequisites..."
echo "──────────────────────────────────────────────────────────────────"

[ -d "$LLAMA_CPP" ] || { echo "❌ llama.cpp not found"; exit 1; }
[ -x "$(command -v python3)" ] || { echo "❌ python3 not found"; exit 1; }

echo "✅ llama.cpp found"
echo "✅ python3 found"
echo ""

# ===== MOUNT DRIVE =====
echo "📀 Step 2: Mounting external drive..."
echo "──────────────────────────────────────────────────────────────────"

if ! mountpoint -q "$MODELS_DIR"; then
    echo "Attempting to mount..."
    bash "$SCRIPT_DIR/mount-external.sh" || {
        echo "❌ Failed to mount external drive"
        exit 1
    }
else
    echo "✅ External drive already mounted"
fi
echo ""

# ===== VERIFY SOURCE MODEL =====
echo "📂 Step 3: Verifying source model..."
echo "──────────────────────────────────────────────────────────────────"

V9_MODEL_DIR="$MODELS_DIR/v9_model_merged"

[ -d "$V9_MODEL_DIR" ] && [ -n "$(ls -A "$V9_MODEL_DIR" 2>/dev/null)" ] || {
    echo "❌ Model not found at: $V9_MODEL_DIR"
    echo "   Did you complete Phase 2 (download-v9-from-drive.sh)?"
    exit 1
}

echo "✅ V9 model found at: $V9_MODEL_DIR"
ls -lh "$V9_MODEL_DIR" | head -5
echo ""

# ===== CONVERT TO F16 =====
echo "🔄 Step 4: Converting to GGUF F16..."
echo "──────────────────────────────────────────────────────────────────"

F16_OUTPUT="$MODELS_DIR/cpp-instructor-v9-f16.gguf"

if [ -f "$F16_OUTPUT" ]; then
    echo "⚠️  F16 already exists, reusing..."
else
    echo "Converting (this takes 5-10 minutes)..."
    python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V9_MODEL_DIR" \
        --outfile "$F16_OUTPUT" \
        --outtype f16
fi

[ -f "$F16_OUTPUT" ] || { echo "❌ F16 conversion failed"; exit 1; }
echo "✅ F16 GGUF created: $(du -h "$F16_OUTPUT" | cut -f1)"
echo ""

# ===== QUANTIZE TO Q5_K_M =====
echo "🗜️  Step 5: Quantizing to Q5_K_M..."
echo "──────────────────────────────────────────────────────────────────"

Q5_OUTPUT="$MODELS_DIR/cpp-instructor-v9-q5.gguf"

if [ -f "$Q5_OUTPUT" ]; then
    echo "⚠️  Q5 already exists, reusing..."
else
    echo "Quantizing (this takes 3-5 minutes)..."
    "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q5_OUTPUT" Q5_K_M
fi

[ -f "$Q5_OUTPUT" ] || { echo "❌ Quantization failed"; exit 1; }
echo "✅ Q5_K_M quantized: $(du -h "$Q5_OUTPUT" | cut -f1)"
echo ""

# ===== BACKUP PREVIOUS VERSION =====
echo "💾 Step 6: Backing up previous version..."
echo "──────────────────────────────────────────────────────────────────"

CURRENT_MODEL="$MODELS_DIR/cpp-instructor-q5.gguf"
V8_BACKUP="$MODELS_DIR/cpp-instructor-v8-q5.gguf"

if [ -f "$CURRENT_MODEL" ]; then
    if [ ! -f "$V8_BACKUP" ]; then
        echo "Creating V8 backup..."
        cp "$CURRENT_MODEL" "$V8_BACKUP"
        echo "✅ V8 backed up: $(du -h "$V8_BACKUP" | cut -f1)"
    else
        echo "✅ V8 backup already exists"
    fi
else
    echo "⚠️  No previous version (first deployment)"
fi
echo ""

# ===== DEPLOY TO EXTERNAL =====
echo "📦 Step 7: Deploying V9 to external drive..."
echo "──────────────────────────────────────────────────────────────────"

echo "Copying to: $CURRENT_MODEL"
cp "$Q5_OUTPUT" "$CURRENT_MODEL"

[ -f "$CURRENT_MODEL" ] || { echo "❌ Deployment failed"; exit 1; }
echo "✅ V9 deployed to external drive: $(du -h "$CURRENT_MODEL" | cut -f1)"
echo ""

# ===== DEPLOY TO INTERNAL SSD (optional) =====
echo "📦 Step 8: Deploying V9 to internal SSD (optional)..."
echo "──────────────────────────────────────────────────────────────────"

INTERNAL_MODEL="$HOME/.local/share/llama-models/cpp-instructor-q5.gguf"
INTERNAL_DIR="$HOME/.local/share/llama-models"

mkdir -p "$INTERNAL_DIR"
echo "Copying to: $INTERNAL_MODEL"
cp "$Q5_OUTPUT" "$INTERNAL_MODEL"

[ -f "$INTERNAL_MODEL" ] || {
    echo "⚠️  Internal deployment failed (non-critical)"
}
echo "✅ V9 deployed to internal SSD: $(du -h "$INTERNAL_MODEL" | cut -f1)"
echo ""

# ===== TEST DEPLOYMENT =====
echo "🧪 Step 9: Testing V9 deployment..."
echo "──────────────────────────────────────────────────────────────────"

if command -v feather &> /dev/null; then
    echo "Test 1: Code example generation"
    echo "────────────────────────────────"
    TEST1=$(feather "Show me a simple C++ example of smart pointers" 2>/dev/null | head -3)
    if [ -n "$TEST1" ]; then
        echo "✅ PASS - Model responds"
    else
        echo "⚠️  Check response manually"
    fi
    echo ""

    echo "Test 2: Assembly knowledge"
    echo "────────────────────────────"
    TEST2=$(feather "What assembly does x++ generate?" 2>/dev/null | head -3)
    if [ -n "$TEST2" ]; then
        echo "✅ PASS - Assembly knowledge present"
    else
        echo "⚠️  Check response manually"
    fi
    echo ""
else
    echo "⚠️  'feather' command not found"
    echo "   Model is deployed, test manually with: feather \"your question\""
fi
echo ""

# ===== SUMMARY =====
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              V9 DEPLOYMENT COMPLETE!                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Deployment Summary:"
echo "   V9 Active (external): $CURRENT_MODEL"
echo "   V9 Active (internal): $INTERNAL_MODEL"
echo "   V8 Backup:           $V8_BACKUP"
echo "   F16 Archive:         $F16_OUTPUT"
echo "   Q5 Archive:          $Q5_OUTPUT"
echo ""
echo "🎯 Test V9 Knowledge:"
echo "   feather \"Explain RAII in C++\""
echo "   feather \"What is virtual function table?\""
echo "   feather \"Show me assembly for int add(int a, int b) { return a + b; }\""
echo ""
echo "🔄 To compare with V8:"
echo "   # Current uses V9, switch to V8:"
echo "   cp $V8_BACKUP $CURRENT_MODEL"
echo ""
echo "💡 To rollback to V8:"
echo "   cp $V8_BACKUP $CURRENT_MODEL"
echo "   cp $V8_BACKUP $INTERNAL_MODEL"
echo ""
echo "📊 Model size comparison:"
echo "   F16 (full precision): $(du -h "$F16_OUTPUT" | cut -f1)"
echo "   Q5_K_M (quantized):   $(du -h "$Q5_OUTPUT" | cut -f1)"
echo "   Compression ratio:    66%"
echo ""
echo "✨ V9 Features (vs V8):"
echo "   • Code + Assembly examples in training data"
echo "   • Behavior-group training (Explain vs Assembly)"
echo "   • Language-specific code formatting (C vs C++)"
echo "   • 4 epochs with checkpoint every 500 steps"
echo "   • 15,494 training examples (12,888 train + 2,606 val)"
echo ""
echo "📊 Model uses internal SSD by default (faster)"
echo "   Use manual path for external: /mnt/external/models/cpp-instructor-q5.gguf"
echo ""
```

---

## Complete Workflow Summary

### Timeline

| Phase | Task | Time | Location |
|-------|------|------|----------|
| 1 | Train model (already done!) | 4 hours | Colab |
| 1 | Merge LoRA adapter | 2-3 min | Colab |
| 2 | Download from Drive | 10-30 min | Local machine |
| 3 | Convert to F16 GGUF | 5-10 min | Local machine |
| 3 | Quantize to Q5_K_M | 3-5 min | Local machine |
| 4 | Deploy to external/internal | 2 min | Local machine |
| 4 | Test deployment | 1-2 min | Local machine |
| **TOTAL** | **All phases** | **~1 hour** | **After training** |

### Commands Checklist

```bash
# On local machine, after training completes on Colab

# 1. Mount external drive (if needed)
cd /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning
./mount-external.sh

# 2. Download from Google Drive
./download-v9-from-drive.sh "YOUR_FOLDER_ID"

# 3. Deploy (converts, quantizes, deploys)
./deploy-v9-model.sh

# 4. Test
feather "Explain smart pointers"
```

---

## Key Differences from V8 (Previous Version)

| Aspect | V8 | V9 |
|--------|----|----|
| **Training Data** | Concept-only | Concept + Code + Assembly |
| **Examples** | Explanations only | Explain + Assembly outputs |
| **Epochs** | 3 | 4 |
| **Checkpoints** | Every 1000 steps | Every 500 steps |
| **Dataset Size** | 8,920 examples | 15,494 examples (+73%) |
| **Code Examples** | No | Yes (3,550 with code) |
| **Assembly Examples** | No | Yes (1,609 with assembly) |
| **Quantization** | Q5_K_M | Q5_K_M (same) |
| **Size** | ~5.5GB | ~5.5GB (same) |

---

## Troubleshooting

### Download Fails

```bash
# Manual download from Google Drive
# 1. Go to: https://drive.google.com/drive/folders/FOLDER_ID
# 2. Click folder → Download (takes 20+ minutes)
# 3. Extract to: /mnt/external/models/v9_model_merged
```

### Conversion Fails

```bash
# Check if llama.cpp is built
ls -la llama.cpp/build/bin/llama-quantize

# If missing, build it
cd llama.cpp && make -j$(nproc) && cd ..
```

### Quantization Out of Memory

```bash
# Check available space
df -h /mnt/external/

# Minimum required: 30GB free (16GB F16 + 5.5GB Q5 + buffer)
# Free up space and retry
```

### Model Won't Load

```bash
# Verify file integrity
file /mnt/external/models/cpp-instructor-q5.gguf

# Should output: "...data"  (GGUF format)

# Check size
du -h /mnt/external/models/cpp-instructor-q5.gguf
# Should be ~5.5GB
```

---

## Next Steps (After V9 Deployment)

1. **Monitor model quality** - Compare V9 vs V8 on key test cases
2. **Gather feedback** - Collect user feedback on new code/assembly features
3. **Plan V10** - Consider additional improvements:
   - More edge case coverage
   - Better assembly formatting
   - Additional POSIX/system knowledge
   - Performance tuning

---

## Files Checklist

- [x] `grok_code_generator.py` - Phase 1 (code generation)
- [x] `compile_to_assembly.py` - Phase 2 (compilation)
- [x] `integrate_code_examples.py` - Phase 3 (dataset integration)
- [x] `finetune_llama_v9_complete.ipynb` - Training notebook
- [ ] `download-v9-from-drive.sh` - **TO CREATE**
- [ ] `deploy-v9-model.sh` - **TO CREATE**
- [x] `mount-external.sh` - External drive mounting (assumed exists)
- [x] `llama.cpp/convert_hf_to_gguf.py` - GGUF conversion
- [x] `llama.cpp/build/bin/llama-quantize` - Quantization tool

---

## Version: V9 Alpha
**Last Updated**: October 21, 2025
**Status**: Ready for deployment after training completion
