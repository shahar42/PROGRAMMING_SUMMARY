# Quick Start Checklist

## ✅ Step 1: Dataset Preparation (COMPLETED!)

**Status:** ✅ DONE

You have successfully created:
- **13,920 training examples** from 2,325 concept files
- Train/validation split: 12,528 / 1,392 (90/10)
- Format: Llama 3.1 chat format (messages with system/user/assistant roles)
- Location: `llama_finetuning/training_data/`

Files created:
- `train.json` - Training data
- `val.json` - Validation data
- `sample.json` - Sample for inspection

---

## 🔲 Step 2: Set Up HuggingFace Account

**Action Required:** Complete this now

### Instructions:

1. **Create Account:**
   - Go to: https://huggingface.co/join
   - Sign up with email

2. **Request Llama Access:**
   - Go to: https://huggingface.co/meta-llama/Llama-3.1-8B
   - Click "Agree and access repository"
   - Fill out the form (usually approved in minutes)

3. **Create Access Token:**
   - Go to: https://huggingface.co/settings/tokens
   - Click "New token"
   - Name: "llama-finetuning"
   - Type: Read
   - Click "Generate"
   - **COPY AND SAVE THIS TOKEN** - you'll need it in Colab

⏱️ Time: 5-10 minutes (including approval wait)

---

## 🔲 Step 3: Upload Dataset to Google Drive

**Action Required:** Do this after Step 2

### Instructions:

1. **Open Google Drive:**
   - Go to: https://drive.google.com
   - Sign in with your Google account

2. **Create Folder:**
   - Click "+ New" → "New folder"
   - Name it: `llama_finetuning`

3. **Upload Files:**
   - Open the `llama_finetuning` folder in Google Drive
   - Click "+ New" → "File upload"
   - Navigate to: `llama_finetuning/training_data/`
   - Upload **both** files:
     - `train.json` (~30-50 MB)
     - `val.json` (~3-5 MB)

4. **Verify Upload:**
   - Confirm both files are visible in Google Drive
   - Path should be: `MyDrive/llama_finetuning/training_data/`

⏱️ Time: 5 minutes

---

## 🔲 Step 4: Open Google Colab

**Action Required:** Do this after Step 3

### Instructions:

1. **Go to Colab:**
   - Visit: https://colab.research.google.com

2. **Upload Notebook:**
   - Click "File" → "Upload notebook"
   - Select: `llama_finetuning/finetune_llama_colab.ipynb`
   - Wait for upload

3. **Change Runtime to GPU:**
   - Click "Runtime" → "Change runtime type"
   - Hardware accelerator: **T4 GPU**
   - Click "Save"

4. **Verify GPU:**
   - Run the first code cell: `!nvidia-smi`
   - Should show "Tesla T4" with ~15GB memory
   - If you see "No GPU available", try:
     - Runtime → Disconnect and delete runtime
     - Runtime → Change runtime type → GPU
     - Try again

⏱️ Time: 2 minutes

---

## 🔲 Step 5: Run Training

**Action Required:** Do this after Step 4

### Instructions:

1. **Follow Notebook:**
   - Run cells in order (press Shift+Enter)
   - Read the instructions in each cell

2. **Enter Your HuggingFace Token:**
   - In Cell 5, replace `YOUR_HUGGINGFACE_TOKEN_HERE`
   - Paste your token from Step 2

3. **Mount Google Drive:**
   - When prompted, click the link
   - Sign in and copy authorization code
   - Paste into Colab

4. **Start Training:**
   - Run all cells up to "Start Fine-Tuning"
   - Training will begin automatically
   - **Go do something else - this takes 2-4 hours**

5. **Monitor Progress:**
   - Training loss should decrease
   - Look for "Training complete!" message

⏱️ Time: 2-4 hours (mostly hands-off)

---

## 🔲 Step 6: Test Your Model

**Action Required:** Do this after training completes

### Instructions:

1. **Save Model:**
   - Run the "Save Your Model" cell
   - Verifies model is saved to Google Drive

2. **Test Model:**
   - Run the "Test Your Model" cell
   - Try the example questions
   - Modify the "Interactive Testing" cell with your questions

3. **Celebrate! 🎉**
   - You now have a fine-tuned Llama model!

⏱️ Time: 5 minutes

---

## 📊 Summary

**Total Time:**
- Hands-on: ~30 minutes
- Training: 2-4 hours (automated)
- **Total: 2.5-4.5 hours**

**What You'll Have:**
- Fine-tuned Llama 3.1 8B model
- Specialized in C/C++ programming instruction
- Trained on 13,920 examples from authoritative sources
- Saved to Google Drive for future use

---

## 🆘 Troubleshooting

### Problem: "No GPU available"
**Solution:**
- Free Colab has limited GPU access
- Try at different times of day
- Consider Colab Pro ($10/month) for guaranteed access

### Problem: "Out of memory"
**Solution:**
- In training configuration cell, change:
  - `per_device_train_batch_size = 1` (instead of 2)
  - Or reduce `max_seq_length = 1024` (instead of 2048)

### Problem: "Can't access Llama model"
**Solution:**
- Verify you accepted the license at huggingface.co/meta-llama/Llama-3.1-8B
- Check your token has "Read" permissions
- Wait a few minutes after accepting license

### Problem: "Training is too slow"
**Solution:**
- This is normal on free T4 GPU
- Upgrade to Colab Pro for A100 access (3-5x faster)
- Or reduce training data size for testing

### Problem: "Session disconnected"
**Solution:**
- Training checkpoints are saved every 500 steps
- Rerun cells and use `resume_from_checkpoint=True`
- Keep browser tab open during training

---

## 💡 Tips

1. **Free Colab Limits:**
   - Sessions timeout after 12 hours
   - GPU access limited during peak times
   - Save model frequently

2. **Best Times to Train:**
   - Late night / early morning (your timezone)
   - Weekdays better than weekends

3. **Monitoring:**
   - Watch the loss curve - should go down
   - Validation loss should track training loss
   - If loss isn't decreasing, check learning rate

4. **After Training:**
   - Download model from Google Drive
   - Upload to HuggingFace Hub (optional)
   - Export to GGUF for local use

---

## 🚀 Next Steps After Successful Fine-Tuning

1. **Share Your Model:**
   - Upload to HuggingFace Hub
   - Share with the community

2. **Further Improvements:**
   - Train for more epochs
   - Fine-tune on specific topics
   - Increase LoRA rank for better quality

3. **Use Your Model:**
   - Build a programming tutor chatbot
   - Create VSCode extension
   - Generate tutorials automatically

4. **Experiment:**
   - Try different hyperparameters
   - Add more training data
   - Test on real programming questions

---

## 📚 Resources

- Step-by-step guide: `STEP_BY_STEP_GUIDE.md`
- Colab notebook: `finetune_llama_colab.ipynb`
- Dataset script: `prepare_dataset.py`
- [Unsloth Docs](https://docs.unsloth.ai)
- [Llama 3.1 Model](https://huggingface.co/meta-llama/Llama-3.1-8B)

---

**Ready to start? Begin with Step 2!** ✨
