# C++ Programming Instructor CLI

Your fine-tuned Llama 3.1 8B model as an interactive command-line tool!

## Quick Start

### 1. Make the script executable
```bash
chmod +x cpp_instructor_cli.py
```

### 2. Run in interactive mode
```bash
python cpp_instructor_cli.py --model /path/to/your/checkpoint-4698
```

Or if you saved to final_model:
```bash
python cpp_instructor_cli.py --model /content/drive/MyDrive/llama_finetuning/final_model
```

### 3. Ask questions!
```
💬 You: Explain smart pointers in C++

🤖 Instructor: Smart pointers in C++ are template classes...
```

---

## Usage Modes

### Interactive Mode (Default)
```bash
python cpp_instructor_cli.py --model /path/to/model
```
- Chat back and forth
- Type 'exit' to quit
- Type 'help' for help
- Type 'clear' to clear screen

### Single Question Mode
```bash
python cpp_instructor_cli.py --model /path/to/model --question "What is RAII?"
```
- Get one answer and exit
- Good for scripting

### Longer Responses
```bash
python cpp_instructor_cli.py --model /path/to/model --max-tokens 800
```
- Default is 512 tokens
- Increase for longer, more detailed answers

---

## Examples

### Ask about pointers
```bash
./cpp_instructor_cli.py -m ./checkpoint-4698 -q "Explain pointers in C"
```

### Interactive session
```bash
./cpp_instructor_cli.py -m ./checkpoint-4698

💬 You: What are templates?
🤖 Instructor: [detailed explanation]

💬 You: Show me an example
🤖 Instructor: [code example]

💬 You: exit
👋 Goodbye!
```

---

## Tips

1. **Be specific** - "Explain virtual functions" is better than "Tell me about C++"
2. **Ask for examples** - Add "with an example" to get code
3. **Follow up** - Ask clarifying questions in the same session
4. **Use max-tokens** - Increase for complex topics that need more explanation

---

## Troubleshooting

### "CUDA out of memory"
- Your GPU doesn't have enough VRAM
- Solution: Use CPU mode (slower):
  ```python
  # Edit cpp_instructor_cli.py, change:
  device_map="auto" → device_map="cpu"
  ```

### "Model not found"
- Check the path to your checkpoint
- Make sure you're pointing to the correct directory
- Should contain `config.json`, `model.safetensors`, etc.

### Slow responses
- First response is always slow (model loading)
- Subsequent responses should be faster
- If using CPU, expect 30-60 seconds per response

---

## Advanced: Using Locally (Not Colab)

If you've downloaded your model to your local machine:

```bash
# Copy from Google Drive
cp -r /path/from/drive/checkpoint-4698 ~/models/cpp-instructor

# Run locally
python cpp_instructor_cli.py --model ~/models/cpp-instructor
```

---

## System Requirements

- **VRAM**: 8GB+ GPU (for 4-bit quantized model)
- **RAM**: 16GB+ system RAM
- **Python**: 3.8+
- **Dependencies**: transformers, torch, accelerate

### Install dependencies:
```bash
pip install transformers torch accelerate
```

---

Enjoy your personal C++ instructor! 🎓
