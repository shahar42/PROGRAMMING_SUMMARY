#!/bin/bash
# Install dependencies for CPU-only inference

echo "Installing PyTorch (CPU-only version)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo ""
echo "Installing other dependencies..."
pip install transformers>=4.35.0
pip install accelerate>=0.20.0
pip install sentencepiece>=0.1.99
pip install protobuf>=3.20.0

echo ""
echo "✅ Installation complete!"
echo ""
echo "⚠️  CPU Warning: Inference will be SLOW (30-60 seconds per response)"
echo "    This is normal for running LLMs on CPU."
echo ""
echo "Next steps:"
echo "1. Download your model from Google Drive"
echo "2. Run: python cpp_instructor_cli.py --model /path/to/checkpoint"
