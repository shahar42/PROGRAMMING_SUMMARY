# Upload to Google Colab - Step by Step

## What You Need to Upload

You need to upload 3 files to Google Drive:

1. ✅ `train.json` (24.4 MB) - Training data
2. ✅ `val.json` (2.7 MB) - Validation data
3. ✅ `.env` (optional but recommended) - Your HuggingFace token

---

## Step 1: Upload Training Data to Google Drive

### Instructions:

1. **Open Google Drive:**
   - Go to: https://drive.google.com
   - Sign in with your Google account

2. **Create Folder Structure:**
   ```
   MyDrive/
   └── llama_finetuning/
       └── training_data/
   ```

   - Click "+ New" → "New folder"
   - Name it: `llama_finetuning`
   - Open that folder
   - Click "+ New" → "New folder" again
   - Name it: `training_data`

3. **Upload Training Files:**
   - Open the `training_data` folder in Google Drive
   - Click "+ New" → "File upload"
   - Navigate to: `llama_finetuning/training_data/`
   - Select and upload:
     - `train.json` (~24 MB)
     - `val.json` (~3 MB)
   - Wait for upload to complete (should take 1-2 minutes)

4. **Upload .env File (Optional but Recommended):**
   - Go back to the `llama_finetuning` folder (not inside training_data)
   - Click "+ New" → "File upload"
   - Navigate to: `llama_finetuning/`
   - Upload: `.env`

   **Note:** If you can't see `.env` file (it's hidden on some systems):
   - On Linux/Mac: Press `Ctrl+H` in file browser to show hidden files
   - On Windows: Enable "Show hidden files" in File Explorer settings

5. **Verify Upload:**
   Your Google Drive should look like this:
   ```
   MyDrive/
   └── llama_finetuning/
       ├── .env                    (your token - keep secret!)
       └── training_data/
           ├── train.json          (24.4 MB)
           └── val.json            (2.7 MB)
   ```

---

## Step 2: Open Google Colab

1. **Go to Colab:**
   - Visit: https://colab.research.google.com

2. **Upload Notebook:**
   - Click "File" → "Upload notebook"
   - Navigate to: `llama_finetuning/finetune_llama_colab.ipynb`
   - Click "Open"

3. **Change Runtime to GPU:**
   - Click "Runtime" → "Change runtime type"
   - Hardware accelerator: Select **"T4 GPU"**
   - Click "Save"

4. **Verify GPU Access:**
   - Run the first code cell (click the play button or Shift+Enter)
   - Should show: "Tesla T4" with ~15GB memory

   **If you see "No GPU available":**
   - Runtime → Disconnect and delete runtime
   - Runtime → Change runtime type → T4 GPU
   - Try again
   - If still no GPU, try at different time or consider Colab Pro

---

## Step 3: Run the Training

### Execute Cells in Order:

1. **Cell 1 - Verify GPU:**
   - Should show Tesla T4
   - ✅ If yes, continue
   - ❌ If no, see troubleshooting above

2. **Cell 2 - Install Dependencies:**
   - Takes ~2 minutes
   - Installs Unsloth, transformers, etc.
   - ✅ Wait for "Successfully installed..." message

3. **Cell 3 - Mount Google Drive:**
   - Click the link that appears
   - Sign in to your Google account
   - Copy the authorization code
   - Paste into Colab
   - Press Enter
   - ✅ Should show "Mounted at /content/drive"

4. **Cell 4 - Load Dataset:**
   - Loads your training data from Google Drive
   - ✅ Should show: "Loaded 12,528 training examples"
   - ✅ Should show: "Loaded 1,392 validation examples"
   - Shows a sample conversation

5. **Cell 5 - Load Llama Model:**
   - **IMPORTANT:** Your token is already in the notebook!
   - If you uploaded `.env`, it will be loaded automatically
   - Takes ~3-5 minutes to download and load model
   - ✅ Should show: "Model loaded successfully!"
   - ✅ Should show memory footprint (~5-6 GB)

6. **Cell 6 - Configure LoRA:**
   - Fast, takes ~30 seconds
   - ✅ Should show trainable parameters count

7. **Cell 7 - Format Dataset:**
   - Converts to Llama 3.1 chat format
   - Takes ~2-3 minutes
   - ✅ Shows formatted example

8. **Cell 8 - Training Configuration:**
   - Sets hyperparameters
   - ✅ Shows training steps estimate

9. **Cell 9 - Create Trainer:**
   - Quick setup
   - ✅ "Trainer created!"

10. **Cell 10 - START TRAINING:**
    - **This takes 2-4 HOURS**
    - You can close the browser tab
    - Training continues in the background
    - Come back in 2-4 hours

11. **Cell 11 - Save Model:**
    - Run this after training completes
    - Saves to Google Drive
    - **IMPORTANT: Don't skip this!**

12. **Cell 12-13 - Test Model:**
    - Try out your fine-tuned model
    - Ask programming questions
    - Celebrate! 🎉

---

## Monitoring Training

While training runs, you'll see output like:

```
Step 10/1566 | Loss: 2.341 | Time: 00:02:15
Step 20/1566 | Loss: 2.198 | Time: 00:04:30
Step 30/1566 | Loss: 2.087 | Time: 00:06:45
...
```

**What to expect:**
- Loss should gradually decrease (2.5 → 1.5 → 1.0 → 0.5)
- Each step takes ~6-8 seconds on T4 GPU
- Total steps: ~1,566 steps
- Total time: 2-4 hours

**Good signs:**
- ✅ Loss is decreasing
- ✅ No "Out of Memory" errors
- ✅ GPU utilization ~90-100%

**Bad signs:**
- ❌ Loss not changing or increasing
- ❌ "CUDA Out of Memory" errors
- ❌ Session disconnected

---

## Troubleshooting

### "Can't find train.json"
**Solution:**
- Check file path in Google Drive
- Should be: `MyDrive/llama_finetuning/training_data/train.json`
- Make sure Drive is mounted (Cell 3)

### "Can't access Llama model"
**Solution:**
- Verify you accepted license at: https://huggingface.co/meta-llama/Llama-3.1-8B
- Check your token is correct in `.env` or notebook
- Wait a few minutes after accepting license

### "CUDA Out of Memory"
**Solution:**
- Edit Cell 8, change:
  ```python
  per_device_train_batch_size = 1  # Instead of 2
  ```
- Or reduce:
  ```python
  max_seq_length = 1024  # Instead of 2048
  ```

### "Session disconnected during training"
**Solution:**
- Training saves checkpoints every 500 steps
- When you reconnect, rerun cells and add to trainer.train():
  ```python
  trainer.train(resume_from_checkpoint=True)
  ```

### "No GPU available"
**Solution:**
- Free Colab has limited GPU access
- Try different time of day (late night/early morning better)
- Consider Colab Pro ($10/month) for guaranteed access

---

## After Training Completes

1. **Save Model (Cell 11):**
   - **CRITICAL:** Run this immediately
   - Saves to Google Drive
   - Session can timeout and you'll lose the model otherwise

2. **Test Model (Cell 12-13):**
   - Try example questions
   - Verify it learned from your data

3. **Download Model:**
   - Go to Google Drive
   - Download: `llama_finetuning/final_model/` folder
   - Keep for future use

4. **Optional - Upload to HuggingFace:**
   ```python
   model.push_to_hub("your-username/llama-cpp-instructor", token=HF_TOKEN)
   ```

---

## Expected Timeline

| Step | Time | Can Close Browser? |
|------|------|-------------------|
| Upload to Drive | 2 min | No |
| Setup Colab | 2 min | No |
| Install deps | 2 min | No |
| Load model | 5 min | No |
| Training | 2-4 hours | ✅ Yes |
| Test model | 5 min | No |

**Total hands-on time:** ~15 minutes
**Total wait time:** 2-4 hours
**Total:** 2-4.25 hours

---

## Your Token Info

- **Token:** `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`
- **Location:** `llama_finetuning/.env`
- **Permissions:** Read access to gated repos
- **Status:** ✅ Ready to use

---

## Files on Your System

Current location: `/home/shahar42/Suumerizing_C_holy_grale_book/llama_finetuning/`

Files ready:
- ✅ `train.json` (12,528 examples)
- ✅ `val.json` (1,392 examples)
- ✅ `.env` (your token)
- ✅ `finetune_llama_colab.ipynb` (updated with token loading)

---

## Quick Checklist

Before starting:
- [ ] Google account signed in
- [ ] Training data uploaded to Drive (`train.json`, `val.json`)
- [ ] `.env` file uploaded to Drive (optional)
- [ ] Colab notebook uploaded
- [ ] GPU runtime selected (T4)
- [ ] HuggingFace Llama access approved

During training:
- [ ] All cells run without errors
- [ ] Training shows decreasing loss
- [ ] Browser tab open or bookmark to return

After training:
- [ ] Model saved to Drive (Cell 11)
- [ ] Model tested successfully (Cell 12-13)
- [ ] Model downloaded for backup

---

**Ready to start? Follow Step 1 above!** ✨
