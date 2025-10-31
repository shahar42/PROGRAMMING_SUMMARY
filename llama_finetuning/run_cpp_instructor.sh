#!/bin/bash

# Run the C++ Instructor model with llama.cpp (fast CPU inference)

MODEL="/mnt/external/models/cpp-instructor-q5.gguf"
LLAMA_BIN="./llama.cpp/build/bin/llama-simple-chat"

if [ ! -f "$MODEL" ]; then
    echo "❌ Model not found at: $MODEL"
    echo "   Run ./convert_to_gguf.sh first!"
    exit 1
fi

echo "🎓 C++ Programming Instructor (Q5_K_M - Optimized)"
echo "================================================================"
echo "📊 Model size: 5.5GB | Fast CPU inference"
echo "================================================================"
echo ""
echo "Type your C++ questions. Press Ctrl+D to exit."
echo ""

$LLAMA_BIN -m "$MODEL"
