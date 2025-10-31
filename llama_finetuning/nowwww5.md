# Llama Fine-Tuning Progress - Current Status (Oct 20, 2025)

## Active Model: V6 Enhanced (Assembly-Level)
- **Location**: `/mnt/external/models/cpp-instructor-q5.gguf` (external) + `~/.local/share/llama-models/cpp-instructor-q5.gguf` (internal SSD, default)
- **Size**: 5.4GB (Q5_K_M quantization)
- **Training**: 3 epochs on assembly-enhanced dataset
- **Status**: Production deployment, accessible via `feather` command

## V7 Dataset: Ready for Training ✅

### V7 Overview - Real Compiler Facts + POSIX Knowledge
V7 is an **accuracy-first** version that fixes V6's hallucinations by using real compiler output instead of AI-generated assembly.

**Key Improvements Over V6:**
- ✅ Real gcc sizeof values (92 types verified with actual compiler)
- ✅ POSIX syscall knowledge (51 syscalls from manpages)
- ✅ Fixed V6 hallucinations (struct padding, array sizes)
- ✅ Improved validation set (critical tests, edge cases, calibration)
- ✅ inline keyword knowledge (ODR compliance, not just optimization)
- ✅ explicit keyword knowledge (constructors only, debunks myths)

**V7 Dataset Stats:**
- **Training**: 10,427 examples (27 MB)
- **Validation**: 1,143 examples (3.3 MB) - **Improved with strategic examples**
- **Total**: 11,570 examples

**Coverage Breakdown:**
- sizeof queries: 213 examples (real compiler output)
- Syscall queries: 1,889 examples (POSIX manpages)
- inline keyword: 17 examples (ODR + optimization myths)
- explicit keyword: 96 examples (constructors/conversion operators)

### V7 vs V6 Critical Fixes

| Issue | V6 (Wrong) | V7 (Fixed) |
|-------|------------|------------|
| struct padding | sizeof(struct { char a; int b; }) = 4 bytes | **8 bytes** (verified with gcc) |
| array sizeof | sizeof(int[3]) = 4 bytes | **12 bytes** (3 × 4 = 12) |
| inline purpose | Optimization hint | **ODR compliance** (primary), optimization obsolete |
| explicit usage | On function templates | **Compile error** - only constructors/conversion operators |
| syscall knowledge | None | 51 syscalls with signatures/errors/flags |

### V7 Validation Set Improvements

**Strategic composition (vs random 10% split):**
- ✅ 5 critical test cases (V6 failure modes)
- ✅ 13 edge cases (unions, volatile, triple pointers, bit fields)
- ✅ 50 hard examples (long, complex multi-step reasoning)
- ✅ 5 calibration examples (ambiguous questions, out-of-scope)
- ✅ 2 adversarial examples (common misconceptions)
- ✅ 1,068 stratified samples (balanced across 8 topic categories)

**Critical tests now in validation:**
- `sizeof(struct { char a; int b; })` → 8 bytes
- `sizeof(int[3])` → 12 bytes
- `sizeof(struct { int a; char b; })` → 8 bytes

### V7 Files Ready for Upload

**Directory**: `fine_tuning_llama_v7_sizeof/`

**Training data:**
- ✅ `train.json` (10,427 examples, 27 MB)
- ✅ `val.json` (1,143 examples, 3.3 MB)
- ✅ `train_before_inline.json` (backup before inline additions)
- ✅ `val_original.json` (backup before improvements)

**Training notebook:**
- ✅ `finetune_llama_v7_colab.ipynb` (updated for V7)
  - 4 epochs (proven effective for V4/V5)
  - max_seq_length: 2048 (V7 has less assembly than V6)
  - batch_size: 4, gradient_accumulation: 2
  - Test questions: V7 critical test cases

**Reference files:**
- ✅ `inline_keyword_additions.json` (5 examples)
- ✅ `explicit_keyword_additions.json` (3 examples)
- ✅ `sizeof_dataset.json` (276 Q&A pairs from 92 verified types)
- ✅ `syscall_dataset.json` (147 Q&A pairs from 51 syscalls)

**Scripts:**
- ✅ `download-v7-from-drive.sh` (downloads trained model)
- ✅ `deploy-v7-model.sh` (complete deployment pipeline with testing)

### V7 Training Parameters

**Colab notebook settings:**
```python
max_seq_length = 2048        # V7: Less assembly than V6
num_train_epochs = 4          # Proven effective for V4/V5
per_device_train_batch_size = 4
gradient_accumulation_steps = 2
effective_batch_size = 8      # 4 × 2
learning_rate = 2e-4
```

**Estimated training time:**
- A100: ~1.5 hours
- T4: ~6 hours

### Next Steps for V7 Deployment

**1. Upload to Google Drive:**
```bash
# Upload entire directory: fine_tuning_llama_v7_sizeof/
# Required files:
#   - train.json (27 MB)
#   - val.json (3.3 MB)
#   - finetune_llama_v7_colab.ipynb
```

**2. Train in Colab:**
- Open `finetune_llama_v7_colab.ipynb`
- Update Drive path
- Run all cells (4 epochs, ~1.5-6 hours)
- Model saves to: `fine_tuning_llama_v7/final_model_merged/`

**3. Download & Deploy:**
```bash
# Download from Drive
./download-v7-from-drive.sh FOLDER_ID

# Deploy (converts to GGUF, quantizes, backs up V6)
./deploy-v7-model.sh
```

**4. Test Critical Cases:**
```bash
# V6 failures that V7 should fix:
feather "What is sizeof(struct { char a; int b; })?"
# Expected: "8 bytes" (V6 said 4 - WRONG)

feather "What is sizeof(int[3])?"
# Expected: "12 bytes" (V6 said 4 - WRONG)

feather "What errno codes can open() return?"
# Expected: Lists EACCES, EINVAL, etc. (V7 POSIX knowledge)

feather "Why do we use inline in header files?"
# Expected: "ODR compliance" (not just optimization)

feather "Can I use explicit on function templates?"
# Expected: "No, compile error - only constructors/conversion operators"
```

## Version History Summary

### V1 (Initial - Sep 2025)
- Basic C++ concepts from books
- 13,920 examples (many duplicates)
- Issues: 56.7% duplicate examples, shallow technical depth

### V2 (Expert-Focused - Oct 2025)
- Deduplication: 13,920 → 6,031 unique
- 56 expert-focused templates
- 18,560 examples → 12,473 after calibration fixes
- Issues: Still had hallucinations on ambiguous questions

### V3 (Curriculum Learning - Oct 2025)
- Concepts processed in structured order (foundational C → advanced C++)
- Deduplicated source concepts
- 4,882 training examples
- Issues: Answer reuse fixed but semantic misalignment warnings

### V4 (Accuracy Rebuild - Oct 2025)
- Complete rebuild from scratch
- Deduplication BEFORE generation
- 8 expert-level question templates
- 9,323 training / 1,036 validation
- Issues: Technically correct but pedagogically wrong (implementation-first)

### V5 (Pedagogical Structure - Oct 2025)
- Teaching-first architecture (WHAT → WHY → HOW → Mistakes → Implementation)
- Top 10 confusing topics restructured
- 9,316 training / 1,036 validation
- Issues: Same theoretical content as V4, still hedged on concrete values

### V5.1 (Bug Fix - Oct 2025)
- Fixed contamination from overly broad regex matching
- Removed 230 contaminated examples
- 9,108 training / 1,014 validation
- Status: Deployed as active model (before V6)

### V6 (Assembly-Enhanced - Oct 2025)
- AI-generated assembly examples (1,710 from Grok/Gemini/GPT-5)
- 12,271 training / 1,364 validation
- max_seq_length: 3072 (for assembly listings)
- Issues: **AI-generated assembly unreliable, hallucinated sizeof values**

### V7 (Real Compiler Facts - Oct 2025) ← **CURRENT, READY FOR TRAINING**
- Real compiler sizeof output (92 types verified)
- POSIX syscall knowledge (51 syscalls from manpages)
- Improved validation set (strategic, not random)
- inline + explicit keyword knowledge
- **10,427 training / 1,143 validation**
- Fixes all V6 hallucinations

## Tools & Scripts

### Active Commands
- `feather` - V6 model CLI (current production)
- `feather --external` - Use external drive version
- `feather2` - Base Llama 3.1 comparison
- `compare-models` - Side-by-side comparison

### Deployment Scripts
- `mount-external.sh` - Auto-mount external drive by label
- `deploy-v7-model.sh` - V7 deployment pipeline (download, convert, quantize, test)
- `download-v7-from-drive.sh` - Download V7 from Google Drive
- `cleanup_old_datasets.sh` - Remove obsolete V2-V6 intermediate files

### Dataset Preparation (V7)
- `improve_validation_set.py` - Created improved V7 validation set
- `fine_tuning_llama_v7_sizeof/generate_sizeof_quick.sh` - Generates 92 sizeof test cases
- `fine_tuning_llama_v7_sizeof/create_sizeof_dataset.py` - Creates Q&A from gcc output
- `fine_tuning_llama_v7_sizeof/extract_syscalls.py` - Extracts from POSIX manpages
- `fine_tuning_llama_v7_sizeof/common_flags.py` - Verified flag definitions

## Model Storage Locations

### External Drive (`/mnt/external/models/`)
- `cpp-instructor-q5.gguf` - V6 active model (5.4GB)
- `cpp-instructor-v6-q5.gguf` - V6 backup (after V7 deployment)
- `cpp-instructor-v5-q5.gguf` - V5 backup
- `cpp-instructor-v4-q5.gguf` - V4 backup
- `cpp-instructor-v1-q5.gguf` - V1 backup
- `Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf` - Base model

### Internal SSD (Default, Faster)
- `~/.local/share/llama-models/cpp-instructor-q5.gguf` - V6 active (default location)

### Model Switching
```bash
feather "question"            # Uses internal SSD (default)
feather --external "question" # Uses external drive
```

## Key Learnings & Design Decisions

### Dataset Quality > Size
- V1: 13,920 examples (56.7% duplicates) → Poor
- V7: 10,427 unique examples → Excellent
- **Lesson**: Deduplication and verification beats raw volume

### AI-Generated Assembly → Unreliable
- V6: Grok/Gemini/GPT-5 generated assembly → Hallucinations
- V7: Real gcc output only → Accurate
- **Lesson**: Use actual tools, not AI guesses

### Validation Sets Need Strategy
- V4-V6: Random 10% split → Missed failure modes
- V7: Strategic (critical tests, edge cases, calibration) → Catches bugs
- **Lesson**: Validation should target known weaknesses

### Pedagogical Structure Helps
- V4: Implementation details first → Buried answers
- V5/V7: WHAT → WHY → HOW → Mistakes → Implementation → Better UX
- **Lesson**: Teaching order matters for user experience

### Platform Specificity is Good
- V5: "depends on platform" → Vague, unhelpful
- V7: "8 bytes on x86-64 Linux gcc" → Concrete, verifiable
- **Lesson**: Platform-specific facts > generic hedging

## Current Status & Readiness

**Production Model:** V6 Enhanced (assembly-level, deployed)
**Next Version:** V7 (real compiler facts, ready for training)

**V7 Readiness Checklist:**
- ✅ Dataset complete (10,427 train / 1,143 val)
- ✅ Validation set improved (strategic examples)
- ✅ Colab notebook updated (paths, epochs, test cases)
- ✅ Deployment scripts ready (download + deploy + test)
- ✅ inline + explicit keywords covered
- ✅ Critical test cases in validation
- ⏳ **Next**: Upload to Google Drive and train

**Expected V7 Impact:**
- Fix sizeof hallucinations (V6's main failure)
- Add POSIX syscall knowledge (new capability)
- Correct inline/explicit understanding (debunk myths)
- Better calibration (knows when to say "I need context")

---

**Last Updated**: Oct 20, 2025, 4:15 PM
**Status**: V7 dataset finalized, awaiting Colab training

  cd /mnt/external/models
  gdown "https://drive.google.com/uc?id=YOUR_FILE_ID" -O model_v9_f16.gguf

  Get file ID from Drive link (share the file, get link, extract ID).

  Or manually download from Drive to /mnt/external/models/.

  Then quantize:

  cd /home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning
  ./llama.cpp/quantize /mnt/external/models/model_v9_f16.gguf /mnt/external/models/model_v9_q5.gguf Q5_K_M

