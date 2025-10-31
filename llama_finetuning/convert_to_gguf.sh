#!/bin/bash

# Convert fine-tuned model to GGUF format for fast CPU inference

echo "🔄 Step 1: Converting model to GGUF (f16)..."
echo "   This will take a few minutes..."

python llama.cpp/convert_hf_to_gguf.py \
    /mnt/external/models/cpp-instructor \
    --outfile /mnt/external/models/cpp-instructor-f16.gguf \
    --outtype f16

echo ""
echo "🔄 Step 2: Quantizing to Q4_K_M (smaller, faster)..."

./llama.cpp/build/bin/llama-quantize \
    /mnt/external/models/cpp-instructor-f16.gguf \
    /mnt/external/models/cpp-instructor-q4.gguf \
    Q4_K_M

echo ""
echo "🗑️  Deleting f16 version to save space..."
rm /mnt/external/models/cpp-instructor-f16.gguf

echo ""
echo "✅ Conversion complete!"
echo "📍 Quantized model: /mnt/external/models/cpp-instructor-q4.gguf"
