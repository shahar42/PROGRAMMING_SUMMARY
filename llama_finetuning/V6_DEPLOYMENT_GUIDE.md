# V6 Enhanced Model Deployment Guide

## Overview
V6 Enhanced is trained with assembly-level content: concrete gcc output, register usage, memory layouts, and platform-specific details (x86-64, System V ABI).

## After Colab Training Completes

### Step 1: Upload Merged Model to Google Drive

In the Colab notebook (Cell 26), the merged model is saved to:
```
/content/drive/MyDrive/fine_tuning_llama_v6_enhanced/final_model_merged
```

**Get the folder ID:**
1. Open Google Drive
2. Navigate to: `fine_tuning_llama_v6_enhanced/final_model_merged/`
3. Right-click the folder → "Get link"
4. Extract ID from: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
5. Copy the `FOLDER_ID_HERE` part

### Step 2: Download V6 Model to External Drive

**Option A: Download script (recommended)**
```bash
cd ~/Suumerizing_C_holy_grale_book/llama_finetuning
./download-v6-from-drive.sh FOLDER_ID
```

**Option B: Manual prompt**
```bash
./download-v6-from-drive.sh
# Will prompt you for folder ID
```

This downloads the ~16GB merged model to `/mnt/external/models/v6_model_merged/`

### Step 3: Deploy V6 Enhanced Model

Run the complete deployment pipeline:
```bash
./deploy-v6-model.sh
```

**What it does:**
1. ✅ Mounts external drive (if not mounted)
2. ✅ Downloads V6 model from Drive (if not already present)
3. ✅ Converts to GGUF F16 format (~15GB)
4. ✅ Quantizes to Q5_K_M (~5.4GB)
5. ✅ Backs up V5 model as `cpp-instructor-v5-q5.gguf`
6. ✅ Deploys V6 as `cpp-instructor-q5.gguf` (active model)
7. ✅ Tests with sample question

**Time estimate:**
- Download: 10-20 minutes (depends on connection)
- Convert: 5-10 minutes
- Quantize: 2-5 minutes
- **Total: ~20-35 minutes**

### Step 4: Test V6 Enhanced Assembly Knowledge

```bash
# Test assembly generation
feather "What assembly does x++ generate?"

# Test memory layout
feather "Show memory layout of struct { char a; int b; }"

# Test register knowledge
feather "What registers are used for function arguments in x86-64?"

# Test virtual functions
feather "How does the compiler implement virtual function calls?"

# Interactive mode
feather
```

### Step 5: Compare V6 vs V5

```bash
compare-models "Explain sizeof(struct { char a; int b; })"
```

**Expected V6 improvements:**
- ✅ Concrete answers: "8 bytes" instead of "depends on platform"
- ✅ Actual assembly: Real `movl $1, %eax` instructions
- ✅ Register usage: Explicit %rdi, %rsi, %rdx documentation
- ✅ Platform calibration: "Typical on x86-64 Linux gcc 13.2, verify with..."

## Rollback to V5 (if needed)

```bash
cp /mnt/external/models/cpp-instructor-v5-q5.gguf \
   /mnt/external/models/cpp-instructor-q5.gguf
```

## File Locations

**On External Drive (`/mnt/external/models/`):**
- `cpp-instructor-q5.gguf` - Active model (V6 after deployment)
- `cpp-instructor-v5-q5.gguf` - V5 backup
- `cpp-instructor-v6-q5.gguf` - V6 standalone
- `cpp-instructor-v6-f16.gguf` - V6 F16 (unquantized)
- `v6_model_merged/` - Downloaded merged model from Colab

## Troubleshooting

### Download fails with gdown
```bash
# Install/update gdown
pip install --upgrade gdown

# Or download manually from Drive and extract to:
/mnt/external/models/v6_model_merged/
```

### External drive not mounted
```bash
./mount-external.sh
```

### llama.cpp not found
```bash
# Script expects llama.cpp at:
~/Suumerizing_C_holy_grale_book/llama_finetuning/llama.cpp/
```

### Quantization binary not found
```bash
cd llama.cpp
mkdir -p build && cd build
cmake ..
make -j$(nproc)
```

## V6 Enhanced Dataset Details

- **Training examples**: 12,271 (assembly-enhanced)
- **Validation examples**: 1,364
- **Assembly coverage**: 27.3% with concrete gcc output
- **Enhancement APIs**: Grok-4-fast + Gemini 2.5 Flash + GPT-5-mini
- **Average answer**: 1,952 chars (488 tokens)
- **Max sequence length**: 3,072 tokens
- **Training epochs**: 3
- **Sources**: K&R C, C++ Primer, CSAPP, C++ Standard + actual compiler output

## Next Steps After Deployment

1. **Test thoroughly** against V4/V5 failure cases
2. **Document improvements** in real-world usage
3. **Prepare V6.1** if additional assembly coverage needed (remaining 570 questions from OpenAI worker)
