# How Fine-Tuning Works: Deep Dive

This document explains EVERYTHING that happens when you fine-tune Llama 3.1, from the fundamental concepts to the specific implementation details.

---

## 🧠 Part 1: What is Fine-Tuning?

### The Analogy

Imagine you have a **general doctor** (base Llama model) who knows medicine broadly. Fine-tuning is like sending them to a **specialized residency** (training on your data) to become a **C++ programming expert**.

### What Actually Happens

1. **Base Model**: Llama 3.1 8B already knows language, reasoning, and some programming
2. **Your Data**: 13,920 examples of C/C++ concept explanations
3. **Fine-Tuning**: Adjust the model's weights so it's REALLY good at explaining C/C++
4. **Result**: A specialized model that talks like your training data

### The Math (Simplified)

```
Base Model Weights + Your Data = Adjusted Weights
```

The model has **8 billion parameters** (numbers). Fine-tuning tweaks these numbers so the model outputs text similar to your training examples.

---

## 🔬 Part 2: Why QLoRA? (The Memory Problem)

### The Problem

Full fine-tuning of Llama 3.1 8B requires:
- **Model**: ~16 GB (in half precision)
- **Optimizer states**: ~32 GB (Adam optimizer keeps momentum)
- **Gradients**: ~16 GB
- **Activations**: ~20+ GB
- **TOTAL**: ~80+ GB of VRAM

**Your T4 GPU**: Only 15 GB 😱

### The Solution: QLoRA

QLoRA = **Q**uantized **Lo**w-**R**ank **A**daptation

It solves the memory problem with THREE tricks:

#### Trick 1: Quantization (4-bit)
```
Normal: Each weight = 32 bits (4 bytes)
4-bit:  Each weight = 4 bits (0.5 bytes)
Savings: 8x less memory!
```

**How it works:**
- Store model weights as 4-bit integers instead of 32-bit floats
- When computing, convert to float temporarily
- Loss of precision is minimal (1-2% accuracy)

**Code:**
```python
load_in_4bit = True  # This triggers 4-bit quantization
```

#### Trick 2: LoRA (Low-Rank Adaptation)
Instead of updating ALL 8 billion parameters, we add small "adapter" layers:

```
Original weight matrix: [4096 x 4096] = 16M parameters
LoRA: Two small matrices: [4096 x 16] and [16 x 4096] = 131k parameters
Savings: 99% fewer trainable parameters!
```

**The Math:**
```
W_new = W_frozen + (A × B)
```
- `W_frozen`: Original weights (frozen, not trained)
- `A × B`: Small matrices we train
- Result: Same output, way less memory

**Code:**
```python
r = 16  # Rank of LoRA matrices (higher = more capacity)
```

#### Trick 3: Gradient Checkpointing
- Don't store ALL intermediate activations
- Recompute them when needed during backpropagation
- Trades compute time for memory

**Result:**
- **Memory**: 10-12 GB (fits on T4!)
- **Quality**: ~95-98% of full fine-tuning
- **Speed**: Slower than full fine-tuning, but possible

---

## 📊 Part 3: The Dataset Format

### Why Llama 3.1 Chat Format?

Llama 3.1 was trained with a specific conversation structure. We must match it:

```json
{
  "messages": [
    {"role": "system", "content": "You are an expert..."},
    {"role": "user", "content": "Explain pointers"},
    {"role": "assistant", "content": "Pointers are..."}
  ]
}
```

### What Happens Behind the Scenes

The tokenizer converts this to:

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert...<|eot_id|><|start_header_id|>user<|end_header_id|>

Explain pointers<|eot_id|><|start_header_id|>assistant<|end_header_id|>

Pointers are...<|eot_id|>
```

These special tokens tell the model:
- When system/user/assistant is talking
- When to stop generating
- The role structure

### Why 6 Variations Per Concept?

```python
# Variation 1: Full explanation
"Explain the programming concept: {topic}"

# Variation 2: Code example
"Can you show me a code example for {topic}?"

# Variation 3: Syntax
"What is the syntax for {topic}?"

# Variation 4: Brief
"Give me a brief explanation of {topic}"

# Variation 5: Conversational
"I'm learning about {topic}. Can you help me understand it?"

# Variation 6: Multi-turn
User: "What is {topic}?"
Assistant: [explains]
User: "Can you show me an example?"
Assistant: [shows code]
```

**Why?** Teaches the model to handle different question styles and multi-turn conversations.

---

## 🎯 Part 4: The Training Process

### Step-by-Step: What Happens

#### 1. Forward Pass
```
Input: "Explain pointers"
→ Tokenize: [4523, 8821, ...]
→ Through model: 8 billion calculations
→ Output: Probability distribution over all tokens
→ Sample: "Pointers"
```

#### 2. Compute Loss
```
Expected: "Pointers are variables that store memory addresses..."
Actual:   "Pointers are variables that store memory addresses..."
Loss = How different these are (cross-entropy)
```

The model tries to predict the next token at each position. Loss is low when predictions match training data.

#### 3. Backpropagation
```
Loss → Gradient (how to adjust weights)
→ Only update LoRA adapters (not frozen base weights)
→ Optimizer (AdamW) adjusts weights
```

#### 4. Repeat
Do this for 12,528 examples, multiple times (epochs).

### Key Hyperparameters Explained

```python
per_device_train_batch_size = 2
```
**What:** Process 2 examples at once
**Why:** T4 GPU can't fit more in memory
**Trade-off:** Smaller = slower training, but works

```python
gradient_accumulation_steps = 4
```
**What:** Accumulate gradients from 4 batches before updating
**Why:** Simulates batch size of 8 (2 × 4)
**Trick:** Gets benefits of larger batch without memory cost

```python
learning_rate = 2e-4
```
**What:** How much to adjust weights each step
**Why:** Too high = unstable, too low = slow
**Magic number:** 2e-4 works well for Llama fine-tuning

```python
num_train_epochs = 1
```
**What:** Go through entire dataset once
**Why:** More epochs = better, but diminishing returns
**Note:** For 13k examples, 1 epoch is often enough

```python
warmup_steps = 50
```
**What:** Gradually increase learning rate for first 50 steps
**Why:** Prevents early training instability
**Analogy:** Like warming up before exercise

```python
optim = "adamw_8bit"
```
**What:** AdamW optimizer in 8-bit precision
**Why:** Standard optimizer but memory efficient
**What it does:** Keeps momentum and adaptive learning rates

```python
lora_alpha = 16
```
**What:** Scaling factor for LoRA updates
**Why:** Controls how much LoRA affects output
**Math:** `alpha / r` = scaling (16/16 = 1.0)

---

## 🔧 Part 5: Code Breakdown

### prepare_dataset.py - What It Does

```python
def concept_to_instruction(concept: Dict) -> List[Dict]:
```

**Purpose:** Convert your JSON concept files to Llama format

**Input:**
```json
{
  "topic": "Pointers in C",
  "explanation": "Pointers are variables...",
  "syntax": "int *ptr;",
  "code_example": ["int x = 5;", "int *ptr = &x;"],
  "example_explanation": "This declares a pointer..."
}
```

**Output:**
```json
{
  "messages": [
    {"role": "system", "content": "You are an expert..."},
    {"role": "user", "content": "Explain the programming concept: Pointers in C"},
    {"role": "assistant", "content": "Pointers are variables...\n\nSyntax:\nint *ptr;\n\n..."}
  ]
}
```

**Why 6 variations?**
- Teaches model flexibility
- Handles different question phrasings
- Enables multi-turn conversations

### The Colab Notebook - Cell by Cell

#### Cell 5: Load Model
```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Meta-Llama-3.1-8B",
    load_in_4bit = True,
)
```

**What happens:**
1. Download Llama 3.1 8B from HuggingFace (if not cached)
2. Load in 4-bit quantized format
3. ~6-8 GB memory usage

**Under the hood:**
- Uses `bitsandbytes` library for quantization
- Weights stored as 4-bit integers
- NF4 (Normal Float 4) quantization for better precision

#### Cell 6: Add LoRA
```python
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", ...],
)
```

**What happens:**
1. Identify which layers to add LoRA to
2. Insert LoRA adapter matrices
3. Freeze original weights
4. Only LoRA matrices are trainable

**Target modules:**
- `q_proj`, `k_proj`, `v_proj`: Query, Key, Value in attention
- `o_proj`: Output projection
- `gate_proj`, `up_proj`, `down_proj`: MLP layers

**Why these?** They're the most important for learning new patterns.

#### Cell 7: Format Dataset
```python
def formatting_prompts_func(examples):
    texts = []
    for messages in examples["messages"]:
        text = tokenizer.apply_chat_template(messages, ...)
        texts.append(text)
    return {"text": texts}
```

**What happens:**
1. Take conversation messages
2. Apply Llama 3.1 chat template
3. Add special tokens (<|start_header_id|>, etc.)
4. Convert to format model expects

**Result:** Raw text with special tokens that the model understands

#### Cell 9: Training Loop
```python
trainer_stats = trainer.train()
```

**What happens (simplified):**
```python
for epoch in range(num_epochs):
    for batch in train_dataset:
        # Forward pass
        outputs = model(batch)
        loss = compute_loss(outputs, targets)

        # Backward pass
        loss.backward()

        # Update weights (every gradient_accumulation_steps)
        if step % gradient_accumulation_steps == 0:
            optimizer.step()
            optimizer.zero_grad()

        # Evaluation
        if step % eval_steps == 0:
            eval_loss = evaluate(val_dataset)
            print(f"Step {step}, Loss: {loss}, Eval Loss: {eval_loss}")
```

**Memory flow:**
1. Load batch (2 examples) → ~2 GB
2. Forward pass → ~3-4 GB activations
3. Backward pass → ~3-4 GB gradients
4. Update LoRA weights → ~0.5 GB
5. **Total:** ~10-12 GB (fits in T4!)

---

## 🎓 Part 6: Why This Works

### The Science

1. **Transfer Learning:**
   - Llama already knows language structure
   - We're just specializing its knowledge
   - Like teaching a general doctor a specialty

2. **Parameter-Efficient Fine-Tuning (PEFT):**
   - Update <1% of parameters
   - Most knowledge stays intact
   - Only adjust what's needed for your domain

3. **Low-Rank Hypothesis:**
   - Most weight updates are low-rank
   - Don't need full matrices
   - Small adapters capture essential changes

### The Results

After training, your model will:
- **Remember:** Base Llama knowledge (language, reasoning)
- **Specialize:** C/C++ concepts from your data
- **Style:** Match the teaching style of your source books
- **Context:** Reference K&R, CSAPP, C++ Primer concepts

### What Makes a Good Fine-Tuned Model?

1. **Data Quality:** Your concepts are well-structured ✅
2. **Data Quantity:** 13,920 examples is excellent ✅
3. **Data Diversity:** Multiple books, multiple question styles ✅
4. **Training Method:** QLoRA is state-of-the-art ✅
5. **Hyperparameters:** We're using proven values ✅

---

## 🔍 Part 7: Under the Hood - Technical Details

### Tokenization Deep Dive

```python
text = "Explain pointers"
tokens = tokenizer(text)
# Result: [4523, 8821]
```

**What's happening:**
1. Text → BPE (Byte Pair Encoding) tokens
2. Each token is a common subword
3. Llama uses 128k vocabulary
4. Special tokens added for chat format

**Example breakdown:**
```
"Explain pointers in C++"
→ ["Explain", "Ġpointers", "Ġin", "ĠC", "++"]
→ [4523, 8821, 304, 356, 1044]
```
(Ġ = space character)

### Attention Mechanism (Why LoRA Targets This)

```
Query (Q) = Input × W_q   ← LoRA here
Key (K)   = Input × W_k   ← LoRA here
Value (V) = Input × W_v   ← LoRA here

Attention = softmax(Q × K^T / √d) × V
Output = Attention × W_o  ← LoRA here
```

**Why add LoRA here?**
- Attention is how the model focuses on relevant context
- Q/K/V determine what information is important
- Fine-tuning attention = learning new patterns

### Memory Breakdown During Training

```
Component                    Memory
─────────────────────────────────────
Base model (4-bit)           6-7 GB
LoRA adapters                0.5 GB
Optimizer states (8-bit)     1 GB
Gradients                    0.5 GB
Activations (batch=2)        2-3 GB
Overhead                     1 GB
─────────────────────────────────────
TOTAL                        ~11-13 GB
```

### Loss Function: Cross-Entropy

```python
# For each token position
predicted_probs = model_output  # [vocab_size]
target_token = ground_truth[position]

loss = -log(predicted_probs[target_token])
```

**What this means:**
- Model outputs probability for each possible next token
- We want high probability for correct token
- Loss is low when model is confident AND correct

**Example:**
```
Target: "pointers"
Model predicts:
  "pointers": 0.85  ← High probability, low loss
  "arrays":   0.10
  "struct":   0.05

vs.

  "pointers": 0.20  ← Low probability, high loss
  "arrays":   0.40
  "struct":   0.40
```

### Optimizer: AdamW (8-bit)

AdamW keeps track of:
1. **Momentum:** Moving average of gradients
2. **Variance:** Moving average of squared gradients
3. **Weight decay:** Regularization

**Why 8-bit?**
- Normal Adam: 32-bit floats for momentum/variance
- 8-bit: Quantized versions
- Saves memory with minimal quality loss

**Update rule:**
```python
m_t = β1 * m_{t-1} + (1-β1) * gradient
v_t = β2 * v_{t-1} + (1-β2) * gradient²
weight = weight - lr * m_t / (√v_t + ε) - λ * weight
```

---

## 📈 Part 8: What to Expect During Training

### Training Curves

**Loss should look like:**
```
Step 0:    Loss: 2.5  ← High at start
Step 100:  Loss: 1.8
Step 500:  Loss: 1.2
Step 1000: Loss: 0.8
Step 2000: Loss: 0.5  ← Lower is better
...
Final:     Loss: 0.3-0.4
```

**What the numbers mean:**
- Loss ~2.5: Random guessing
- Loss ~1.0: Learning patterns
- Loss ~0.5: Pretty good
- Loss ~0.3: Excellent

### Validation vs Training Loss

```
Training Loss:   How well model fits training data
Validation Loss: How well model generalizes

Good:
  Train: 0.3, Val: 0.35  ← Close together

Overfitting:
  Train: 0.1, Val: 0.8   ← Big gap, model memorized training data

Underfitting:
  Train: 1.5, Val: 1.6   ← Both high, model not learning
```

### Timeline

```
Minutes 0-10:   Setup, loading model
Minutes 10-20:  First 100 steps (should see loss drop quickly)
Hour 1:         Loss plateauing around 0.8-1.0
Hour 2:         Loss around 0.5-0.6
Hour 3-4:       Final convergence to 0.3-0.4
```

---

## 💡 Part 9: Advanced Concepts

### Why Gradient Accumulation Works

```python
# Normal batch size 8 (won't fit)
for batch in get_batches(data, batch_size=8):
    loss = model(batch)
    loss.backward()
    optimizer.step()  # Update every batch

# With gradient accumulation (fits!)
for i, batch in enumerate(get_batches(data, batch_size=2)):
    loss = model(batch)
    loss.backward()  # Accumulate gradients

    if (i+1) % 4 == 0:
        optimizer.step()  # Update every 4 batches
        optimizer.zero_grad()
```

**Result:** Same updates as batch size 8, but 4x less memory!

### Rank (r) in LoRA - Intuition

```
Low rank (r=4):   Small adapter, less capacity, faster
                  Good for: Small datasets, simple tasks

Medium rank (r=16): Balanced (recommended)
                    Good for: Most use cases

High rank (r=64):  Large adapter, more capacity, slower
                   Good for: Large datasets, complex tasks
```

**Your case:** r=16 is perfect for 13k examples

### Why Max Sequence Length Matters

```python
max_seq_length = 2048
```

- Each example is tokenized to ≤2048 tokens
- Longer = more context, more memory
- 2048 = ~1500 words, good for your concept explanations

**Memory scaling:**
```
1024 tokens: ~1 GB per batch
2048 tokens: ~2 GB per batch
4096 tokens: ~4 GB per batch
```

---

## 🎯 Part 10: Practical Insights

### What Makes Your Data Special

1. **High Quality:** Extracted from authoritative books
2. **Well-Structured:** Topic, explanation, syntax, code, example
3. **Diverse:** Multiple programming books and styles
4. **Real Concepts:** Not synthetic, but real teaching content
5. **Multi-Modal:** Text + code + examples

### What the Model Learns

**Explicit Knowledge:**
- C/C++ syntax
- Programming concepts
- Code patterns
- Best practices

**Implicit Knowledge:**
- Teaching style
- How to structure explanations
- When to show code examples
- How to reference source material

### Why 1 Epoch Might Be Enough

```
13,920 examples ÷ (batch_size 2 × grad_accum 4) = ~1,740 steps

At each step:
- Model sees 8 examples (effective batch size)
- Updates LoRA weights
- Learns patterns

After 1,740 steps:
- Model has seen all concepts
- Weights adjusted to your domain
- Additional epochs = diminishing returns
```

**When to train more:**
- Loss still decreasing
- Validation loss improving
- Have time for longer training

---

## 🚀 Part 11: What Happens After Training

### Model Weights

Before:
```
llama_3.1_8b/
  ├── model.safetensors  (16 GB - frozen)
  └── config.json
```

After:
```
your_finetuned_model/
  ├── adapter_model.safetensors  (~50 MB - your LoRA adapters!)
  ├── adapter_config.json
  └── [base model loaded separately]
```

**Key insight:** You only save 50 MB of adapters, not the whole 16 GB model!

### Inference

```python
# Load base model
base_model = load("llama-3.1-8b", 4bit=True)

# Load your adapters
model = add_lora_adapters(base_model, "your_adapters.safetensors")

# Now it's specialized!
output = model.generate("Explain pointers")
```

### Merging (Optional)

You can merge LoRA adapters into base model:
```python
merged_model = merge_lora(base_model, adapters)
# Now it's a standalone 16 GB model with your specialization baked in
```

**Trade-off:**
- Merged: Easier to use, 16 GB
- LoRA: More flexible, 50 MB adapters + 16 GB base

---

## 📚 Further Reading

### Core Papers
1. **LoRA:** https://arxiv.org/abs/2106.09685
2. **QLoRA:** https://arxiv.org/abs/2305.14314
3. **Llama 3.1:** https://ai.meta.com/blog/meta-llama-3-1/

### Key Concepts to Research
- Transformer architecture
- Attention mechanisms
- PEFT (Parameter-Efficient Fine-Tuning)
- Quantization techniques
- Transfer learning

### Hands-On Learning
After fine-tuning, experiment with:
- Different learning rates
- More epochs
- Different LoRA ranks
- Different target modules
- Additional training data

---

## ❓ Common Questions

### Q: Why not full fine-tuning?
**A:** Would need 80+ GB VRAM. QLoRA gets 95-98% of the quality at 1/8 the memory.

### Q: Can I use CPU?
**A:** Yes, but 100x slower. A 4-hour GPU training = 400 hours on CPU.

### Q: Why Llama 3.1 vs other models?
**A:** Open-source, high quality, good community support, optimized tooling (Unsloth).

### Q: Will it forget base knowledge?
**A:** No! LoRA only adjusts specific patterns. Base knowledge stays intact.

### Q: How much does Colab Pro help?
**A:** A100 is ~5x faster than T4. Worth it for frequent training.

### Q: Can I fine-tune further?
**A:** Yes! You can fine-tune your fine-tuned model on more specific data.

### Q: How do I know if training is working?
**A:** Loss should decrease. Test on validation set. Generate sample outputs.

### Q: What if I run out of memory?
**A:** Reduce batch size to 1, reduce max_seq_length to 1024, or reduce LoRA rank to 8.

---

## 🎓 You Now Understand

✅ What fine-tuning is and why it works
✅ Why QLoRA solves the memory problem
✅ How the dataset format affects learning
✅ What each hyperparameter does
✅ What happens during training
✅ How the model learns your domain
✅ Why this approach is effective
✅ How to interpret training metrics

**You're not just running code - you understand the science!** 🚀

