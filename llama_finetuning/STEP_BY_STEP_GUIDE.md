# Step-by-Step Guide: Fine-Tuning Llama 3.1 on Google Colab

## 📋 Overview

We're going to fine-tune Llama 3.1 8B using:
- **Method**: QLoRA (most efficient for free GPU)
- **Library**: Unsloth (optimized for Colab)
- **GPU**: Google Colab T4 (free tier)
- **Data**: Your 4,500+ programming concepts
- **Time**: ~2-8 hours total

## ✅ Step 1: Prepare Dataset Locally (NO GPU NEEDED)

This step runs on your PC without any GPU:

```bash
cd llama_finetuning
python3 prepare_dataset.py
```

**What this does:**
- Converts your concept JSON files to Llama 3.1 chat format
- Creates training variations (6 different question styles per concept)
- Splits into train/validation sets (90/10)
- Generates ~20,000-27,000 training examples

**Expected output:**
```
✅ Found 4512 concept files
📊 Generated ~25000 training examples
💾 Saved datasets:
   Training: training_data/train.json (22500 examples)
   Validation: training_data/val.json (2500 examples)
```

**Check the sample:**
```bash
cat training_data/sample.json | python3 -m json.tool | less
```

---

## ✅ Step 2: Set Up HuggingFace Account

1. Go to https://huggingface.co/join
2. Create a free account
3. Go to https://huggingface.co/meta-llama/Llama-3.1-8B
4. Accept the license agreement (required to access Llama models)
5. Go to https://huggingface.co/settings/tokens
6. Create a new token with "Read" permissions
7. **Save this token** - you'll need it in Colab

---

## ✅ Step 3: Upload Dataset to Google Drive

1. Go to https://drive.google.com
2. Create a folder called `llama_finetuning`
3. Upload your `training_data` folder (train.json and val.json)
   - These files will be ~50-100MB total

---

## ✅ Step 4: Open Google Colab

1. Go to https://colab.research.google.com
2. Click "New Notebook"
3. **IMPORTANT**: Change runtime to GPU
   - Click Runtime → Change runtime type
   - Hardware accelerator: **T4 GPU**
   - Click Save

4. Verify GPU is available:
```python
!nvidia-smi
```

You should see output showing a T4 GPU with ~15GB memory.

---

## ✅ Step 5: Set Up Colab Environment

Copy and run these cells in your Colab notebook:

### Cell 1: Install Dependencies
```python
# Install Unsloth and dependencies (optimized for Llama 3.1)
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes
```

### Cell 2: Mount Google Drive
```python
from google.colab import drive
drive.mount('/content/drive')
```

### Cell 3: Load Dataset
```python
import json

# Load your training data
with open('/content/drive/MyDrive/llama_finetuning/training_data/train.json', 'r') as f:
    train_data = json.load(f)

with open('/content/drive/MyDrive/llama_finetuning/training_data/val.json', 'r') as f:
    val_data = json.load(f)

print(f"Loaded {len(train_data)} training examples")
print(f"Loaded {len(val_data)} validation examples")

# Show a sample
print("\nSample conversation:")
print(json.dumps(train_data[0], indent=2))
```

---

## ✅ Step 6: Load Llama 3.1 Model with QLoRA

### Cell 4: Load Model
```python
from unsloth import FastLanguageModel
import torch

# Model configuration
max_seq_length = 2048  # Maximum length of conversations
dtype = None  # Auto-detect
load_in_4bit = True  # Use 4-bit quantization for QLoRA

# Load Llama 3.1 8B
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Meta-Llama-3.1-8B",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
    token = "YOUR_HUGGINGFACE_TOKEN_HERE"  # Replace with your token from Step 2
)

print("✅ Model loaded successfully!")
print(f"Model memory footprint: {model.get_memory_footprint() / 1e9:.2f} GB")
```

### Cell 5: Configure LoRA
```python
# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,  # LoRA rank
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth",  # Memory efficient
    random_state = 3407,
)

print("✅ LoRA adapters added!")
```

---

## ✅ Step 7: Prepare Data for Training

### Cell 6: Format Dataset
```python
from datasets import Dataset

# Convert to HuggingFace Dataset format
train_dataset = Dataset.from_list(train_data)
val_dataset = Dataset.from_list(val_data)

print(f"Training dataset: {len(train_dataset)} examples")
print(f"Validation dataset: {len(val_dataset)} examples")
```

---

## ✅ Step 8: Configure Training

### Cell 7: Training Configuration
```python
from trl import SFTTrainer
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir = "./outputs",
    per_device_train_batch_size = 2,  # Small batch for T4
    gradient_accumulation_steps = 4,  # Simulate batch size of 8
    warmup_steps = 50,
    max_steps = 1000,  # Adjust based on dataset size
    learning_rate = 2e-4,
    fp16 = not torch.cuda.is_bf16_supported(),
    bf16 = torch.cuda.is_bf16_supported(),
    logging_steps = 10,
    optim = "adamw_8bit",  # Memory efficient optimizer
    weight_decay = 0.01,
    lr_scheduler_type = "linear",
    seed = 3407,
    save_strategy = "steps",
    save_steps = 500,
    evaluation_strategy = "steps",
    eval_steps = 100,
    load_best_model_at_end = True,
)

print("✅ Training configuration ready!")
```

---

## ✅ Step 9: Start Fine-Tuning

### Cell 8: Create Trainer and Start Training
```python
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = train_dataset,
    eval_dataset = val_dataset,
    dataset_text_field = "messages",  # Our chat format field
    max_seq_length = max_seq_length,
    args = training_args,
)

# Start training!
print("🚀 Starting training...")
print("This will take 2-8 hours on T4 GPU")
print("You can close the browser - training will continue")

trainer_stats = trainer.train()

print("✅ Training complete!")
print(trainer_stats)
```

**What to expect:**
- Training will show progress bars
- Loss should decrease over time
- You'll see periodic evaluation metrics
- **Time**: 2-4 hours for ~22k examples on T4

---

## ✅ Step 10: Save Your Model

### Cell 9: Save Fine-Tuned Model
```python
# Save to Google Drive so you don't lose it
model.save_pretrained("/content/drive/MyDrive/llama_finetuning/final_model")
tokenizer.save_pretrained("/content/drive/MyDrive/llama_finetuning/final_model")

print("✅ Model saved to Google Drive!")
```

---

## ✅ Step 11: Test Your Model

### Cell 10: Test the Model
```python
# Test your fine-tuned model
FastLanguageModel.for_inference(model)

def ask_model(question):
    messages = [
        {"role": "system", "content": "You are an expert programming instructor specializing in C and C++."},
        {"role": "user", "content": question}
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize = True,
        add_generation_prompt = True,
        return_tensors = "pt"
    ).to("cuda")

    outputs = model.generate(
        input_ids = inputs,
        max_new_tokens = 512,
        temperature = 0.7,
        top_p = 0.9,
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Test it!
print("Testing model...")
response = ask_model("Explain the concept of pointers in C")
print(response)
```

---

## 🎉 Success Checklist

- ✅ Dataset prepared locally
- ✅ HuggingFace account created and Llama access granted
- ✅ Dataset uploaded to Google Drive
- ✅ Colab notebook running with T4 GPU
- ✅ Model fine-tuned successfully
- ✅ Model saved to Google Drive
- ✅ Model tested and responding

---

## 📊 Expected Results

Your fine-tuned model should:
- Explain C/C++ concepts in detail
- Provide relevant code examples
- Follow the teaching style from your source books
- Handle questions about pointers, memory, STL, etc.
- Reference concepts from K&R, CSAPP, C++ Primer

---

## 💡 Tips & Troubleshooting

### Out of Memory Error?
- Reduce `per_device_train_batch_size` to 1
- Reduce `max_seq_length` to 1024
- Enable `gradient_checkpointing`

### Colab Disconnected?
- Training progress is saved at checkpoints
- Resume from last checkpoint using `resume_from_checkpoint=True`

### Training Too Slow?
- Upgrade to Colab Pro ($10/month) for longer sessions
- Reduce `max_steps` for quicker initial results
- Use fewer training examples for testing

### Want Better Quality?
- Train for more epochs (increase `max_steps`)
- Increase `r` (LoRA rank) to 32 or 64
- Use A100 GPU (Colab Pro+)

---

## 🚀 Next Steps

After successful fine-tuning:
1. Export model to GGUF format for local use (llama.cpp)
2. Upload to HuggingFace Hub to share
3. Use in your own applications
4. Fine-tune further on specific topics

---

## 📚 Additional Resources

- [Unsloth Documentation](https://docs.unsloth.ai)
- [Llama 3.1 Model Card](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Google Colab Pro](https://colab.research.google.com/signup)
