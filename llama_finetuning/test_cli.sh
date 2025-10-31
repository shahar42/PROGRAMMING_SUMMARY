#!/bin/bash
# Quick test of the CLI with sample questions

MODEL_PATH="/content/drive/MyDrive/llama_fine_tuning/checkpoints/checkpoint-4698"

echo "Testing C++ Instructor CLI..."
echo "=============================="
echo ""

echo "Test 1: What are pointers?"
python cpp_instructor_cli.py --model "$MODEL_PATH" --question "What are pointers in C++?" --max-tokens 300

echo ""
echo "=============================="
echo ""

echo "Test 2: Explain RAII"
python cpp_instructor_cli.py --model "$MODEL_PATH" --question "What is RAII?" --max-tokens 300

echo ""
echo "=============================="
echo "Tests complete!"
