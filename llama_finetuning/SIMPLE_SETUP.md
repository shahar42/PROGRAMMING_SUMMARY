# Simplest Local Setup - 3 Steps

## Step 1: Export in Colab (5 minutes)

In your Colab notebook, copy the file `export_for_local.py` and run it.

This will:
- Merge your LoRA adapter with the base model
- Save a standard HuggingFace format to Google Drive
- Create `final_model_merged` folder (~16GB)

## Step 2: Download (~30 min on fast connection)

1. Go to Google Drive
2. Find: `llama_finetuning/final_model_merged`
3. Download entire folder
4. Extract to: `~/models/cpp-instructor`

## Step 3: Install & Run (5 minutes)

```bash
# Install dependencies (one-time)
pip install torch transformers --index-url https://download.pytorch.org/whl/cpu

# Run interactive mode
python cpp_instructor_simple.py --model ~/models/cpp-instructor

# Or single question
python cpp_instructor_simple.py \
  --model ~/models/cpp-instructor \
  --question "Explain smart pointers"
```

---

## That's It!

**Total size:** ~16GB merged model
**No base model needed:** Everything is merged
**No LoRA complexity:** Standard transformers only
**Works offline:** No internet needed after download

---

## Expected Performance

- **First load:** 2-5 minutes
- **Each answer:** 30-60 seconds (CPU)
- **RAM usage:** ~12-14GB

---

## Troubleshooting

**"Out of memory"**
- Close other applications
- You need 16GB RAM minimum

**"Model not found"**
- Check path: `~/models/cpp-instructor` should contain `config.json`

**Very slow**
- Normal on CPU! 30-60 sec per response is expected
- Consider using RunPod/Vast.ai GPU for faster inference
