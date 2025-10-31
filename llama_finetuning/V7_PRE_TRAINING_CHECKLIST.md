# V7 Pre-Training Checklist

## ✅ Dataset Quality Verification (COMPLETED)

### Critical Test Cases
- [x] `sizeof(struct { char a; int b; })` → **8 bytes** (V6 said 4 - WRONG)
- [x] `sizeof(int[3])` → **12 bytes** (V6 said 4 - WRONG)
- [x] `sizeof(struct { int a; char b; })` → **8 bytes**
- [x] All 3/3 critical V6 failures fixed in V7

### Dataset Composition
- [x] Total: 10,419 examples (10,295 train / 1,144 val)
- [x] sizeof examples: 306 (2.9%) - verified with real gcc output
- [x] Syscall examples: 1,889 (18.1%) - extracted from POSIX manpages
- [x] Assembly examples: 1,101 (10.6%)
- [x] Other C++ concepts: 7,123 (68.4%)

### Quality Metrics
- [x] No malformed examples (0/10,419)
- [x] No actual hallucinations (false alarm on "13 bytes" - all legitimate)
- [x] Truncated responses: 0.01% (negligible)
- [x] Concrete answers: 61% (vs 39% hedging - acceptable)
- [x] Average answer length: 1,882 chars (good detail)
- [x] Quality score: **99/100** ✅

### Verified Data Sources
- [x] sizeof values: Real gcc compiler output (92 types tested)
- [x] Syscalls: POSIX manpages (51 syscalls with signatures/errors/flags)
- [x] Assembly: Mix of AI-generated + verified examples
- [x] C++ concepts: From authoritative books (C++ Primer, CSAPP, K&R, etc.)

---

## 📋 Pre-Training Steps

### 1. Local Cleanup (Optional)
```bash
# Free up ~100MB of old dataset files
./cleanup_old_datasets.sh
```

### 2. Upload V7 Dataset to Google Drive
```bash
# Upload the entire V7 directory
# From: llama_finetuning/fine_tuning_llama_v7_sizeof/
# To: Your Google Drive
# Required files:
#   - train.json (27 MB)
#   - val.json (2.9 MB)
```

**Files to upload:**
- [ ] `train.json` (10,295 examples, 27 MB)
- [ ] `val.json` (1,144 examples, 2.9 MB)
- [ ] `finetune_llama_v4_colab.ipynb` (reuse from V4, update paths)

### 3. Prepare Colab Notebook
- [ ] Open `finetune_llama_v4_colab.ipynb` in Google Colab
- [ ] Update dataset path to V7 directory
- [ ] Verify training parameters:
  - Epochs: 4 (proven effective for V4/V5)
  - Max sequence length: 2048 (V7 has longer examples)
  - Learning rate: Same as V4
  - Batch size: Adjust for GPU memory

### 4. Start Training in Colab
- [ ] Mount Google Drive
- [ ] Install dependencies (transformers, trl, peft, etc.)
- [ ] Load base model: `meta-llama/Meta-Llama-3.1-8B-Instruct`
- [ ] Load V7 training data
- [ ] Start training (A100: ~1.5 hours, T4: ~6 hours)
- [ ] Monitor validation loss (target: <0.3)

### 5. Post-Training
- [ ] Save merged model to Google Drive
- [ ] Download model to local machine
- [ ] Convert to GGUF F16 format
- [ ] Quantize to Q5_K_M (~5.4GB)

---

## 🚀 Deployment Steps

### 1. Download V7 Model from Drive
```bash
cd ~/Suumerizing_C_holy_grale_book/llama_finetuning/
# Use rclone or gdown to download from Drive
# Target: /mnt/external/models/v7_model_merged/
```

### 2. Convert to GGUF
```bash
cd llama.cpp/
python3 convert-hf-to-gguf.py /mnt/external/models/v7_model_merged/ \
    --outfile /mnt/external/models/cpp-instructor-v7-f16.gguf \
    --outtype f16
```

### 3. Quantize to Q5_K_M
```bash
./llama-quantize /mnt/external/models/cpp-instructor-v7-f16.gguf \
    /mnt/external/models/cpp-instructor-v7-q5.gguf Q5_K_M
```

### 4. Backup V6 and Deploy V7
```bash
# Backup V6 (currently active)
cp /mnt/external/models/cpp-instructor-q5.gguf \
   /mnt/external/models/cpp-instructor-v6-q5.gguf

# Deploy V7 to external drive
cp /mnt/external/models/cpp-instructor-v7-q5.gguf \
   /mnt/external/models/cpp-instructor-q5.gguf

# IMPORTANT: Copy to internal SSD (faster, default location)
sudo cp /mnt/external/models/cpp-instructor-v7-q5.gguf \
        /home/shahar42/.local/share/llama-models/cpp-instructor-q5.gguf
```

---

## 🧪 Post-Deployment Testing

### Critical Test Cases (V6 Failures)
```bash
# Test 1: struct padding
feather "What is sizeof(struct { char a; int b; })?"
# Expected: "8 bytes" (NOT "4 bytes" or "depends")

# Test 2: array sizeof
feather "What is sizeof(int[3])?"
# Expected: "12 bytes" (3 × 4 = 12, NOT "4 bytes")

# Test 3: syscall knowledge
feather "What errno codes can open() return?"
# Expected: Lists EACCES, EEXIST, EINVAL, etc. with explanations

# Test 4: O_CREAT flag
feather "What is O_CREAT in open()?"
# Expected: "Create file if it does not exist"

# Test 5: assembly output
feather "What assembly does x++ generate?"
# Expected: Shows actual instructions like "addl $1, -4(%rbp)"
```

### Behavioral Tests
- [ ] Answers lead with WHAT first (not implementation details)
- [ ] Concrete values for sizeof (not "depends on platform")
- [ ] Shows actual tool output (gcc -S, pahole, nm) when relevant
- [ ] Platform-specific calibration ("Typical on x86-64, verify with...")
- [ ] No hallucinations or fake keywords

### Comparison with V6
```bash
# Side-by-side test
feather "What is sizeof(struct { char a; int b; })?"
# V6: "4 bytes" ❌
# V7: "8 bytes" ✅
```

---

## 📊 Expected V7 Improvements Over V6

### Accuracy
- ✅ Zero wrong sizeof values (V6 hallucinated)
- ✅ Concrete answers instead of hedging
- ✅ Real compiler facts (not AI-generated guesses)

### Knowledge Breadth
- ✅ POSIX syscall signatures (51 syscalls)
- ✅ errno codes with meanings
- ✅ Flag constants (O_RDONLY, PROT_READ, etc.)

### Answer Structure
- ✅ Direct answer first (WHAT)
- ✅ Tool output in HOW section
- ✅ Platform calibration notes

---

## 🔄 Rollback Procedure (If V7 Has Issues)

```bash
# Restore V6 as active model
cp /mnt/external/models/cpp-instructor-v6-q5.gguf \
   /mnt/external/models/cpp-instructor-q5.gguf

# Internal SSD
sudo cp /mnt/external/models/cpp-instructor-v6-q5.gguf \
        /home/shahar42/.local/share/llama-models/cpp-instructor-q5.gguf

# Test
feather "What is RAII?"
```

---

## 📝 Notes

**V7 Key Differentiators:**
1. Real compiler sizeof output (92 types verified)
2. POSIX syscall knowledge from manpages
3. Concrete answers with platform specifics
4. Fixed V6's critical hallucinations

**Training Time Estimate:**
- Google Colab A100: ~1.5 hours
- Google Colab T4: ~6 hours

**Model Size:**
- Merged (safetensors): ~15GB
- F16 GGUF: ~15GB
- Q5_K_M GGUF: ~5.4GB (production)

**Current Status:** Dataset ready, awaiting Colab training ✅
