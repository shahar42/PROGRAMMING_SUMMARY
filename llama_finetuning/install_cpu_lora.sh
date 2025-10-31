#!/bin/bash
# Install dependencies for CPU-only LoRA inference

echo "Installing PyTorch (CPU-only version)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "Installing Transformers and PEFT..."
pip install transformers>=4.35.0
pip install peft>=0.7.0
pip install accelerate>=0.20.0
pip install sentencepiece>=0.1.99
pip install protobuf>=3.20.0

echo ""
echo "✅ Installation complete!"
echo ""
echo "⚠️  CPU Warning: Inference will be SLOW (30-60 seconds per response)"
echo ""
echo "Next steps:"
echo "1. Download base Llama 3.1 8B model"
echo "2. Download your checkpoint-4698 folder from Google Drive"
echo "3. Run: python cpp_instructor_cli_lora.py --base-model PATH --adapter PATH"
