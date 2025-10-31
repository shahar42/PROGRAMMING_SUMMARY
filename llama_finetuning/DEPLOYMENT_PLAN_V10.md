# V10 Model Deployment Plan
## Download, Quantize & Deploy Pipeline

**Status**: Waiting for training completion on Colab
**Target**: Deploy fine-tuned Llama 3.1 8B C/C++ instructor (Enriched Assembly) to external drive

---

## Overview

The V10 deployment pipeline consists of 3 main phases:

1. **Merge LoRA Adapter** - Combine LoRA weights with base Llama 3.1 8B (Colab)
2. **Download from Drive** - Transfer merged model to external drive (Local)
3. **Deploy Pipeline** - Convert, quantize, backup old model, deploy new one (Local)

---

## Phase 1: Merge LoRA Adapter (On Colab)

**Location**: Cell 24 in `finetune_llama_v10_assembly.ipynb`
**Time**: 2-3 minutes
**Output**: `/content/drive/MyDrive/fine_tuning_llama_v9_clean/checkpoints_v9_improved/model_v9_merged` (~16GB)

After training completes, run Cell 24 to merge the model. The cell automatically:
- Finds the best checkpoint
- Merges LoRA adapter with base model
- Saves to Google Drive in checkpoints folder

---

## Phase 2: Download from Google Drive (Local)

**Script**: `./download-v10-from-drive.sh`
**Time**: 10-30 minutes (depends on connection, ~16GB)
**Requires**: External drive mounted at `/mnt/external`
**Output**: `/mnt/external/models/v10_model_merged`

### Get Google Drive Folder ID

1. After merge completes in Colab
2. Go to Google Drive
3. Navigate to: `fine_tuning_llama_v9_clean/checkpoints_v9_improved/model_v9_merged`
4. Right-click folder → **Get link**
5. Extract ID from: `https://drive.google.com/drive/folders/FOLDER_ID`

### Run Download

```bash
cd /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning

# Provide folder ID as argument
./download-v10-from-drive.sh "YOUR_FOLDER_ID_HERE"

# Or run without args to be prompted
./download-v10-from-drive.sh
```

---

## Phase 3: Deploy Pipeline (Local)

**Script**: `./deploy-v10-model.sh`
**Time**: ~20 minutes total
**Requires**: External drive mounted, llama.cpp built

### What It Does Automatically

1. ✅ Mounts external drive (if needed)
2. ✅ Verifies downloaded model
3. ✅ Converts to F16 GGUF (~5-10 min)
4. ✅ Quantizes to Q5_K_M (~3-5 min)
5. ✅ Backs up V9 model to external drive
6. ✅ **Deletes old internal SSD model to free space**
7. ✅ Deploys V10 to external drive
8. ✅ Deploys V10 to internal SSD
9. ✅ Tests deployment with sample queries

### Run Deployment

```bash
./deploy-v10-model.sh
```

The script is fully automated with progress indicators and error handling.

---

## Key Differences from V9

| Aspect | V9 | V10 |
|--------|----|----|
| **Dataset Size** | 15,494 examples | 12,267 examples (more focused) |
| **Assembly Coverage** | ~10% | 37.6% (4,616 examples) |
| **Assembly Quality** | Raw compiler output | Cleaned (no metadata) |
| **Learning Rate** | 1e-4 | 2e-4 (optimized) |
| **Epochs** | 4 | 2 (avoid overfitting) |
| **Data Sources** | Limited | ALL available data merged |
| **Focus** | Broad | Deep low-level understanding |

---

## V10 Improvements

### Dataset Enhancements
- ✅ Merged ALL available data (155MB + 73MB previously unused files)
- ✅ 12,267 total examples (9,813 train + 2,454 val)
- ✅ 4,616 assembly Q&A pairs (37.6% coverage)
- ✅ Cleaned assembly output (removed compiler metadata/boilerplate)

### Training Optimizations
- ✅ Learning rate: 2e-4 (Perplexity-recommended for this dataset)
- ✅ Weight decay: 0.05 (better regularization)
- ✅ 2 epochs (prevent overfitting on technical domain)
- ✅ Warmup steps: 200 (smooth learning rate ramp)

### Deployment Automation
- ✅ Automatic backup of V9
- ✅ Automatic deletion of old internal model (saves space)
- ✅ Deploys to both external drive and internal SSD
- ✅ Automated testing after deployment

---

## Complete Workflow Summary

### Commands Checklist

```bash
# After training completes on Colab:

# 1. Download from Google Drive
cd /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning
./download-v10-from-drive.sh "YOUR_FOLDER_ID"

# 2. Deploy (does everything automatically)
./deploy-v10-model.sh

# 3. Test
./feather "Explain smart pointers"
./feather "Show me assembly for int add(int a, int b) { return a + b; }"
```

### Timeline

| Phase | Task | Time | Location |
|-------|------|------|----------|
| 1 | Train model | ~3-4 hours | Colab |
| 1 | Merge LoRA adapter | 2-3 min | Colab |
| 2 | Download from Drive | 10-30 min | Local |
| 3 | Convert to F16 GGUF | 5-10 min | Local |
| 3 | Quantize to Q5_K_M | 3-5 min | Local |
| 3 | Backup & deploy | 2 min | Local |
| 3 | Test deployment | 1-2 min | Local |
| **TOTAL** | **All phases** | **~1 hour** | **After training** |

---

## Expected Capabilities

V10 should excel at:
- ✅ Accurate x86-64 assembly generation for C++ code
- ✅ Deep understanding of compiler behavior and optimizations
- ✅ Memory layout, vtables, and object models
- ✅ Prefix/postfix operators, inheritance, pointers (with assembly proof)
- ✅ Low-level language semantics and implementation details
- ✅ RAII, move semantics, virtual functions

---

## File Locations After Deployment

```
External Drive (/mnt/external/models/):
  cpp-instructor-q5.gguf          # V10 active model
  cpp-instructor-v10-q5.gguf      # V10 archive
  cpp-instructor-v10-f16.gguf     # V10 F16 archive
  cpp-instructor-v9-q5.gguf       # V9 backup
  v10_model_merged/               # Downloaded HF model

Internal SSD ($HOME/models/):
  cpp-instructor-q5.gguf          # V10 active (feather uses this)

Feather Script:
  /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning/feather
  (Will automatically use internal SSD model for faster access)
```

---

## Rollback to V9

If V10 has issues:

```bash
# Restore V9 from backup
cp /mnt/external/models/cpp-instructor-v9-q5.gguf /mnt/external/models/cpp-instructor-q5.gguf
cp /mnt/external/models/cpp-instructor-v9-q5.gguf $HOME/models/cpp-instructor-q5.gguf

# Test
./feather "Explain pointers"
```

---

## Troubleshooting

### External drive not mounted
```bash
sudo mount /dev/sdX /mnt/external  # Replace sdX with your drive
# Or check existing mount:
lsblk
```

### Download fails
- Try manual download from Google Drive web interface
- Extract to `/mnt/external/models/v10_model_merged`
- Run deploy script

### Quantization out of memory
```bash
# Check free space
df -h /mnt/external/

# Need: ~30GB free (16GB F16 + 5.5GB Q5 + buffer)
```

### Model won't load in feather
```bash
# Check file integrity
file $HOME/models/cpp-instructor-q5.gguf
# Should show GGUF format

# Check size
du -h $HOME/models/cpp-instructor-q5.gguf
# Should be ~5.5GB
```

---

## Version: V10 Alpha
**Last Updated**: October 22, 2025
**Status**: Ready for deployment after training completion
**Expected Training Completion**: After ~3-4 hours on A100
