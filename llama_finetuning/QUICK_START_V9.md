# V9 Deployment - Quick Start Guide

**Status**: Training completed ✅ | Ready for deployment

---

## 🚀 Quick Commands

```bash
cd /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning

# After training finishes, on Colab:
# 1. Run colab_merge_v9.py cell (merge LoRA adapter)

# On local machine:
# 2. Get folder ID from Google Drive (model_v9_merged folder)
# 3. Download model from Drive
./download-v9-from-drive.sh "YOUR_FOLDER_ID_HERE"

# 4. Deploy (converts, quantizes, deploys)
./deploy-v9-model.sh

# 5. Test
feather "Explain smart pointers in C++"
```

---

## 📋 Step-by-Step

### Step 1: Merge LoRA Adapter (Colab - 2-3 min)

```python
# In Colab notebook after training:
# 1. Create new cell
# 2. Copy-paste content from: colab_merge_v9.py
# 3. Run cell

# Output: /content/drive/MyDrive/fine_tuning_llama_v9_clean/model_v9_merged
```

### Step 2: Get Google Drive Folder ID

1. Go to: https://drive.google.com/drive/my-drive
2. Navigate: `fine_tuning_llama_v9_clean` → `model_v9_merged`
3. Right-click folder → **Get link**
4. Copy URL: `https://drive.google.com/drive/folders/1abc2def3ghi...`
5. Extract ID: `1abc2def3ghi...`

### Step 3: Download Model (Local - 10-30 min)

```bash
# Mount external drive
./mount-external.sh

# Download from Drive
./download-v9-from-drive.sh "1abc2def3ghi"

# Wait for download to complete (~16GB)
```

### Step 4: Deploy Model (Local - 15-20 min)

```bash
./deploy-v9-model.sh

# Automatic steps:
# 1. Convert HF → GGUF F16 (5-10 min)
# 2. Quantize F16 → Q5_K_M (3-5 min)
# 3. Deploy to external drive
# 4. Deploy to internal SSD
# 5. Test model
```

### Step 5: Test Model

```bash
# Test code examples
feather "Show me a C++ smart pointer example"

# Test assembly
feather "What assembly does x++ generate?"

# Test both C and C++
feather "What's the difference between malloc and new?"
```

---

## 📊 File Locations

| Purpose | Path | Size |
|---------|------|------|
| Source (from Drive) | `/mnt/external/models/v9_model_merged` | ~16GB |
| F16 GGUF | `/mnt/external/models/cpp-instructor-v9-f16.gguf` | ~16GB |
| Q5 GGUF | `/mnt/external/models/cpp-instructor-v9-q5.gguf` | ~5.5GB |
| **Active Model (External)** | `/mnt/external/models/cpp-instructor-q5.gguf` | ~5.5GB |
| **Active Model (Internal)** | `~/.local/share/llama-models/cpp-instructor-q5.gguf` | ~5.5GB |
| V8 Backup | `/mnt/external/models/cpp-instructor-v8-q5.gguf` | ~5.5GB |

---

## ⏱️ Timeline

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Train model | 4 hours | ✅ Done |
| 1 | Merge LoRA | 2-3 min | ⏳ After training |
| 2 | Download from Drive | 10-30 min | ⏳ Next |
| 3 | Convert to GGUF | 5-10 min | ⏳ Next |
| 3 | Quantize to Q5 | 3-5 min | ⏳ Next |
| 4 | Deploy | 2 min | ⏳ Next |
| 4 | Test | 1-2 min | ⏳ Next |
| **TOTAL** | **All after training** | **~1 hour** | ⏳ Waiting |

---

## 🔧 Troubleshooting

### "❌ External drive not mounted!"
```bash
./mount-external.sh
# Then retry the deployment script
```

### "❌ gdown not installed!"
```bash
pip install gdown
# Then retry the download script
```

### "❌ Model directory empty or missing"
- Check Drive: Is model_v9_merged folder present?
- Check local: `ls -la /mnt/external/models/v9_model_merged/`
- Retry download with correct folder ID

### "❌ F16 conversion failed"
- Check Python: `python3 --version`
- Check llama.cpp: `ls -la llama.cpp/convert_hf_to_gguf.py`
- Check disk space: `df -h /mnt/external/`

### "❌ Q5 quantization failed"
- Check llama.cpp build: `ls -la llama.cpp/build/bin/llama-quantize`
- If missing: `cd llama.cpp && make -j$(nproc) && cd ..`

### Model produces no output
```bash
# Check model loads
feather "test"

# If fails, check model exists
file /mnt/external/models/cpp-instructor-q5.gguf
# Should show GGUF format

# Check size
du -h /mnt/external/models/cpp-instructor-q5.gguf
# Should be ~5.5GB
```

---

## 🔄 Rollback to V8

If V9 has issues, quickly revert:

```bash
# Switch to V8 (one command)
cp /mnt/external/models/cpp-instructor-v8-q5.gguf \
   /mnt/external/models/cpp-instructor-q5.gguf

# Verify
feather "test question"
```

---

## 📈 What's New in V9

| Feature | V8 | V9 |
|---------|----|----|
| Training data | Concepts only | Concepts + Code + Assembly |
| Examples | Explanations | Explain + Assembly outputs |
| Dataset size | 8,920 examples | 15,494 examples (+73%) |
| Epochs | 3 | 4 |
| Checkpoint freq | 1000 steps | 500 steps |
| Code examples | None | 3,550 |
| Assembly examples | None | 1,609 |
| Model size | 5.5GB | 5.5GB (same) |

---

## 🎯 Test Cases

```bash
# Code examples
feather "Show me a C++ smart pointer example"
feather "What is RAII?"

# Assembly
feather "What assembly does x++ generate?"
feather "Show me assembly for an if-statement"

# C vs C++
feather "Difference between malloc and new"
feather "What is a constructor?"

# Both languages
feather "Explain pointers in C"
feather "Explain references in C++"
```

---

## 📞 Issues?

Check full plan: `cat DEPLOYMENT_PLAN_V9.md`

Scripts: `ls -la deploy* download* colab*`

Logs: All scripts output to console (no log files)

---

## ✨ Done!

After `./deploy-v9-model.sh` completes:

✅ V9 active on external drive
✅ V9 active on internal SSD
✅ V8 backed up for rollback
✅ Model tested and verified
✅ Ready for production use

**Total time**: ~1 hour from training completion to deployment

---

**Created**: October 21, 2025
**Version**: V9 Alpha
**Status**: Ready for deployment
