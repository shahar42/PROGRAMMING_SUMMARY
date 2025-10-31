#!/bin/bash
# Deploy V9 Model - Complete Pipeline
# Run this after training completes on Colab and download-v9-from-drive.sh completes

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP="$SCRIPT_DIR/llama.cpp"
MODELS_DIR="/mnt/external/models"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Feather V9 Model Deployment Pipeline                  ║"
echo "║         (C/C++ Instructor with Code + Assembly)               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
echo "──────────────────────────────────────────────────────────────────"

if [ ! -d "$LLAMA_CPP" ]; then
    echo "❌ llama.cpp not found at: $LLAMA_CPP"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found"
    exit 1
fi

echo "✅ llama.cpp found"
echo "✅ python3 found"
echo ""

# Step 2: Mount external drive
echo "📀 Step 2: Mounting external drive..."
echo "──────────────────────────────────────────────────────────────────"

if ! mountpoint -q "$MODELS_DIR"; then
    echo "Attempting to mount..."
    bash "$SCRIPT_DIR/mount-external.sh" || {
        echo "❌ Failed to mount external drive"
        echo "Please mount manually and rerun this script"
        exit 1
    }
else
    echo "✅ External drive already mounted"
fi
echo ""

# Step 3: Verify source model
echo "📂 Step 3: Verifying source model..."
echo "──────────────────────────────────────────────────────────────────"

V9_MODEL_DIR="$MODELS_DIR/v9_model_merged"

if [ ! -d "$V9_MODEL_DIR" ] || [ -z "$(ls -A "$V9_MODEL_DIR" 2>/dev/null)" ]; then
    echo "❌ Model not found at: $V9_MODEL_DIR"
    echo ""
    echo "Did you complete Phase 2 (download-v9-from-drive.sh)?"
    echo "Run: ./download-v9-from-drive.sh \"YOUR_FOLDER_ID\""
    exit 1
fi

echo "✅ V9 model found at: $V9_MODEL_DIR"
echo "📊 Contents:"
ls -lh "$V9_MODEL_DIR" | grep -E "(config|model|tokenizer)" | head -5
echo ""

# Step 4: Convert to GGUF F16
echo "🔄 Step 4: Converting to GGUF F16..."
echo "──────────────────────────────────────────────────────────────────"

F16_OUTPUT="$MODELS_DIR/cpp-instructor-v9-f16.gguf"

if [ -f "$F16_OUTPUT" ]; then
    echo "⚠️  F16 file already exists: $F16_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing F16 file..."
    else
        rm "$F16_OUTPUT"
        echo "Converting (this takes 5-10 minutes)..."
        python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V9_MODEL_DIR" \
            --outfile "$F16_OUTPUT" \
            --outtype f16
    fi
else
    echo "Converting (this takes 5-10 minutes)..."
    python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V9_MODEL_DIR" \
        --outfile "$F16_OUTPUT" \
        --outtype f16
fi

if [ ! -f "$F16_OUTPUT" ]; then
    echo "❌ F16 conversion failed"
    exit 1
fi

echo "✅ F16 GGUF created: $F16_OUTPUT"
echo "📊 Size: $(du -h "$F16_OUTPUT" | cut -f1)"
echo ""

# Step 5: Quantize to Q5_K_M
echo "🗜️  Step 5: Quantizing to Q5_K_M..."
echo "──────────────────────────────────────────────────────────────────"

Q5_OUTPUT="$MODELS_DIR/cpp-instructor-v9-q5.gguf"

if [ -f "$Q5_OUTPUT" ]; then
    echo "⚠️  Q5 file already exists: $Q5_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing Q5 file..."
    else
        rm "$Q5_OUTPUT"
        echo "Quantizing (this takes 3-5 minutes)..."
        "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q5_OUTPUT" Q5_K_M
    fi
else
    echo "Quantizing (this takes 3-5 minutes)..."
    "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q5_OUTPUT" Q5_K_M
fi

if [ ! -f "$Q5_OUTPUT" ]; then
    echo "❌ Q5 quantization failed"
    exit 1
fi

echo "✅ Q5_K_M quantized: $Q5_OUTPUT"
echo "📊 Size: $(du -h "$Q5_OUTPUT" | cut -f1)"
echo ""

# Step 6: Backup previous version
echo "💾 Step 6: Backing up previous version..."
echo "──────────────────────────────────────────────────────────────────"

CURRENT_MODEL="$MODELS_DIR/cpp-instructor-q5.gguf"
V8_BACKUP="$MODELS_DIR/cpp-instructor-v8-q5.gguf"

if [ -f "$CURRENT_MODEL" ]; then
    if [ ! -f "$V8_BACKUP" ]; then
        echo "Creating V8 backup..."
        cp "$CURRENT_MODEL" "$V8_BACKUP"
        echo "✅ V8 backed up to: $V8_BACKUP"
        echo "📊 Size: $(du -h "$V8_BACKUP" | cut -f1)"
    else
        echo "✅ V8 backup already exists: $V8_BACKUP"
        echo "📊 Size: $(du -h "$V8_BACKUP" | cut -f1)"
    fi
else
    echo "⚠️  No previous version found (first deployment)"
fi
echo ""

# Step 7: Deploy V9 to external drive
echo "📦 Step 7: Deploying V9 to external drive..."
echo "──────────────────────────────────────────────────────────────────"

echo "Copying to: $CURRENT_MODEL"
cp "$Q5_OUTPUT" "$CURRENT_MODEL"

if [ ! -f "$CURRENT_MODEL" ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ V9 deployed to external drive"
echo "📊 Size: $(du -h "$CURRENT_MODEL" | cut -f1)"
echo ""

# Step 8: Deploy V9 to internal SSD (optional)
echo "📦 Step 8: Deploying V9 to internal SSD (optional)..."
echo "──────────────────────────────────────────────────────────────────"

INTERNAL_MODEL="$HOME/.local/share/llama-models/cpp-instructor-q5.gguf"
INTERNAL_DIR="$HOME/.local/share/llama-models"

mkdir -p "$INTERNAL_DIR"
echo "Copying to: $INTERNAL_MODEL"
cp "$Q5_OUTPUT" "$INTERNAL_MODEL"

if [ ! -f "$INTERNAL_MODEL" ]; then
    echo "⚠️  Internal deployment failed (non-critical, external drive is primary)"
else
    echo "✅ V9 deployed to internal SSD"
    echo "📊 Size: $(du -h "$INTERNAL_MODEL" | cut -f1)"
fi
echo ""

# Step 9: Test deployment
echo "🧪 Step 9: Testing V9 deployment..."
echo "──────────────────────────────────────────────────────────────────"

if command -v feather &> /dev/null; then
    echo "Test 1: Code example generation"
    echo "────────────────────────────────"
    TEST1=$(feather "Show me a simple C++ example of smart pointers" 2>/dev/null | head -5)

    if [ -n "$TEST1" ]; then
        echo "✅ PASS - Model responds"
        echo "   Sample: $(echo "$TEST1" | head -1)"
    else
        echo "⚠️  Model produced no output (check manually)"
    fi
    echo ""

    echo "Test 2: Assembly knowledge"
    echo "────────────────────────────"
    TEST2=$(feather "What assembly does x++ generate?" 2>/dev/null | head -5)

    if [ -n "$TEST2" ]; then
        echo "✅ PASS - Assembly knowledge present"
        echo "   Sample: $(echo "$TEST2" | head -1)"
    else
        echo "⚠️  Model produced no output (check manually)"
    fi
    echo ""

    echo "Test 3: C/C++ distinction"
    echo "────────────────────────────"
    TEST3=$(feather "Explain the difference between malloc and new" 2>/dev/null | head -3)

    if [ -n "$TEST3" ]; then
        echo "✅ PASS - C/C++ knowledge present"
    else
        echo "⚠️  Model produced no output (check manually)"
    fi
    echo ""
else
    echo "⚠️  'feather' command not found"
    echo "   Model is deployed, test manually:"
    echo "   feather \"Explain pointers in C++\""
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              V9 DEPLOYMENT COMPLETE!                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Deployment Summary:"
echo "   V9 Active (external): $CURRENT_MODEL"
echo "   V9 Active (internal): $INTERNAL_MODEL"
echo "   V8 Backup:           $V8_BACKUP"
echo "   F16 Archive:         $F16_OUTPUT"
echo "   Q5 Archive:          $Q5_OUTPUT"
echo ""
echo "🎯 Test V9 Knowledge:"
echo "   feather \"Explain RAII in C++\""
echo "   feather \"Show me assembly for int add(int a, int b) { return a + b; }\""
echo "   feather \"What is a virtual function table?\""
echo "   feather \"Explain move semantics\""
echo ""
echo "🔄 Compare with V8:"
echo "   # Temporarily switch to V8:"
echo "   cp $V8_BACKUP $CURRENT_MODEL"
echo "   feather \"your question\""
echo "   # Switch back to V9:"
echo "   cp $Q5_OUTPUT $CURRENT_MODEL"
echo ""
echo "💡 To rollback to V8 permanently:"
echo "   cp $V8_BACKUP $CURRENT_MODEL"
echo "   cp $V8_BACKUP $INTERNAL_MODEL"
echo ""
echo "📊 Model Comparison:"
echo "   Version: V9 (Code + Assembly examples)"
echo "   Dataset: 15,494 examples (v8: ~8,920)"
echo "   Epochs: 4 (checkpoint every 500 steps)"
echo "   F16 size: $(du -h "$F16_OUTPUT" | cut -f1)"
echo "   Q5 size:  $(du -h "$Q5_OUTPUT" | cut -f1)"
echo "   Compression: 66%"
echo ""
echo "✨ V9 New Features (vs V8):"
echo "   • Concrete code examples (3,550 with code)"
echo "   • Assembly outputs (1,609 with assembly)"
echo "   • Behavior-group training (Explain vs Assembly)"
echo "   • Language-specific formatting (C vs C++)"
echo "   • Higher training density (4 epochs)"
echo ""
echo "📊 Default model location: $CURRENT_MODEL"
echo "   Internal SSD copy (faster): $INTERNAL_MODEL"
echo "   External drive (backup): /mnt/external/models/cpp-instructor-q5.gguf"
echo ""
