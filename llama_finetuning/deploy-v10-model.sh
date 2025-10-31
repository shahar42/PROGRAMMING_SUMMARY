#!/bin/bash
# Deploy V10 Model - Complete Pipeline
# Run this after training completes on Colab and download-v10-from-drive.sh completes

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP="$SCRIPT_DIR/llama.cpp"
MODELS_DIR="/mnt/external/models"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Feather V10 Model Deployment Pipeline                 ║"
echo "║         (Enriched Assembly + Deep C++ Understanding)          ║"
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
        echo "Please mount manually: sudo mount /dev/sdX /mnt/external"
        exit 1
    }
else
    echo "✅ External drive already mounted"
fi
echo ""

# Step 3: Verify source model
echo "📂 Step 3: Verifying source model..."
echo "──────────────────────────────────────────────────────────────────"

V10_MODEL_DIR="$MODELS_DIR/v10_model_merged"

if [ ! -d "$V10_MODEL_DIR" ] || [ -z "$(ls -A "$V10_MODEL_DIR" 2>/dev/null)" ]; then
    echo "❌ Model not found at: $V10_MODEL_DIR"
    echo ""
    echo "Did you complete download-v10-from-drive.sh?"
    echo "Run: ./download-v10-from-drive.sh \"YOUR_FOLDER_ID\""
    exit 1
fi

echo "✅ V10 model found at: $V10_MODEL_DIR"
echo "📊 Contents:"
ls -lh "$V10_MODEL_DIR" | grep -E "(config|model|tokenizer)" | head -5
echo ""

# Step 4: Convert to GGUF F16
echo "🔄 Step 4: Converting to GGUF F16..."
echo "──────────────────────────────────────────────────────────────────"

F16_OUTPUT="$MODELS_DIR/cpp-instructor-v10-f16.gguf"

if [ -f "$F16_OUTPUT" ]; then
    echo "⚠️  F16 file already exists: $F16_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing F16 file..."
    else
        rm "$F16_OUTPUT"
        echo "Converting (this takes 5-10 minutes)..."
        python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V10_MODEL_DIR" \
            --outfile "$F16_OUTPUT" \
            --outtype f16
    fi
else
    echo "Converting (this takes 5-10 minutes)..."
    python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V10_MODEL_DIR" \
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

# Step 5: Quantize to Q6_K
echo "🗜️  Step 5: Quantizing to Q6_K..."
echo "──────────────────────────────────────────────────────────────────"

Q6_OUTPUT="$MODELS_DIR/cpp-instructor-v10-q6.gguf"

if [ -f "$Q6_OUTPUT" ]; then
    echo "⚠️  Q6 file already exists: $Q6_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing Q6 file..."
    else
        rm "$Q6_OUTPUT"
        echo "Quantizing (this takes 3-5 minutes)..."
        "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q6_OUTPUT" Q6_K
    fi
else
    echo "Quantizing (this takes 3-5 minutes)..."
    "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q6_OUTPUT" Q6_K
fi

if [ ! -f "$Q6_OUTPUT" ]; then
    echo "❌ Q6 quantization failed"
    exit 1
fi

echo "✅ Q6_K quantized: $Q6_OUTPUT"
echo "📊 Size: $(du -h "$Q6_OUTPUT" | cut -f1)"
echo ""

# Step 6: Backup previous version and delete old internal model
echo "💾 Step 6: Managing previous versions..."
echo "──────────────────────────────────────────────────────────────────"

CURRENT_MODEL_EXTERNAL="$MODELS_DIR/cpp-instructor-q5.gguf"
CURRENT_MODEL_INTERNAL="$HOME/models/cpp-instructor-q5.gguf"
V9_BACKUP="$MODELS_DIR/cpp-instructor-v9-q5.gguf"

# Backup current v9 from external drive
if [ -f "$CURRENT_MODEL_EXTERNAL" ]; then
    if [ ! -f "$V9_BACKUP" ]; then
        echo "Creating V9 backup on external drive..."
        cp "$CURRENT_MODEL_EXTERNAL" "$V9_BACKUP"
        echo "✅ V9 backed up to: $V9_BACKUP"
        echo "📊 Size: $(du -h "$V9_BACKUP" | cut -f1)"
    else
        echo "✅ V9 backup already exists: $V9_BACKUP"
        echo "📊 Size: $(du -h "$V9_BACKUP" | cut -f1)"
    fi
else
    echo "⚠️  No previous version found on external drive (first deployment)"
fi

# Delete old internal model (feather script's model) to free space
if [ -f "$CURRENT_MODEL_INTERNAL" ]; then
    echo "🗑️  Deleting old internal model to free space..."
    rm "$CURRENT_MODEL_INTERNAL"
    echo "✅ Deleted: $CURRENT_MODEL_INTERNAL"
    echo "   (Will be replaced with V10)"
else
    echo "⚠️  No internal model found (nothing to delete)"
fi

echo ""

# Step 7: Deploy V10 to external drive
echo "📦 Step 7: Deploying V10 to external drive..."
echo "──────────────────────────────────────────────────────────────────"

echo "Copying to: $CURRENT_MODEL_EXTERNAL"
cp "$Q6_OUTPUT" "$CURRENT_MODEL_EXTERNAL"

if [ ! -f "$CURRENT_MODEL_EXTERNAL" ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ V10 deployed to external drive"
echo "📊 Size: $(du -h "$CURRENT_MODEL_EXTERNAL" | cut -f1)"
echo ""

# Step 8: Deploy V10 to internal SSD
echo "📦 Step 8: Deploying V10 to internal SSD..."
echo "──────────────────────────────────────────────────────────────────"

INTERNAL_DIR="$HOME/models"

mkdir -p "$INTERNAL_DIR"
echo "Copying to: $CURRENT_MODEL_INTERNAL"
cp "$Q6_OUTPUT" "$CURRENT_MODEL_INTERNAL"

if [ ! -f "$CURRENT_MODEL_INTERNAL" ]; then
    echo "⚠️  Internal deployment failed (non-critical, external drive is primary)"
else
    echo "✅ V10 deployed to internal SSD"
    echo "📊 Size: $(du -h "$CURRENT_MODEL_INTERNAL" | cut -f1)"
fi
echo ""

# Step 9: Test deployment
echo "🧪 Step 9: Testing V10 deployment..."
echo "──────────────────────────────────────────────────────────────────"

FEATHER_SCRIPT="$SCRIPT_DIR/feather"

if [ -f "$FEATHER_SCRIPT" ]; then
    echo "Test 1: Code example generation"
    echo "────────────────────────────────"
    TEST1=$("$FEATHER_SCRIPT" "Show me a simple C++ example of smart pointers" 2>/dev/null | head -5)

    if [ -n "$TEST1" ]; then
        echo "✅ PASS - Model responds"
        echo "   Sample: $(echo "$TEST1" | head -1)"
    else
        echo "⚠️  Model produced no output (check manually)"
    fi
    echo ""

    echo "Test 2: Assembly knowledge"
    echo "────────────────────────────"
    TEST2=$("$FEATHER_SCRIPT" "What assembly does x++ generate?" 2>/dev/null | head -5)

    if [ -n "$TEST2" ]; then
        echo "✅ PASS - Assembly knowledge present"
        echo "   Sample: $(echo "$TEST2" | head -1)"
    else
        echo "⚠️  Model produced no output (check manually)"
    fi
    echo ""

    echo "Test 3: C/C++ distinction"
    echo "────────────────────────────"
    TEST3=$("$FEATHER_SCRIPT" "Explain the difference between malloc and new" 2>/dev/null | head -3)

    if [ -n "$TEST3" ]; then
        echo "✅ PASS - C/C++ knowledge present"
    else
        echo "⚠️  Model produced no output (check manually)"
    fi
    echo ""
else
    echo "⚠️  'feather' script not found at: $FEATHER_SCRIPT"
    echo "   Model is deployed, test manually:"
    echo "   $FEATHER_SCRIPT \"Explain pointers in C++\""
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              V10 DEPLOYMENT COMPLETE!                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Deployment Summary:"
echo "   V10 Active (external): $CURRENT_MODEL_EXTERNAL"
echo "   V10 Active (internal): $CURRENT_MODEL_INTERNAL"
echo "   V9 Backup:            $V9_BACKUP"
echo "   F16 Archive:          $F16_OUTPUT"
echo "   Q6 Archive:           $Q6_OUTPUT"
echo ""
echo "🎯 Test V10 Knowledge:"
echo "   $FEATHER_SCRIPT \"Explain RAII in C++\""
echo "   $FEATHER_SCRIPT \"Show me assembly for int add(int a, int b) { return a + b; }\""
echo "   $FEATHER_SCRIPT \"What is a virtual function table?\""
echo "   $FEATHER_SCRIPT \"Explain move semantics\""
echo ""
echo "🔄 Compare with V9:"
echo "   # Temporarily switch to V9:"
echo "   cp $V9_BACKUP $CURRENT_MODEL_EXTERNAL"
echo "   $FEATHER_SCRIPT \"your question\""
echo "   # Switch back to V10:"
echo "   cp $Q6_OUTPUT $CURRENT_MODEL_EXTERNAL"
echo ""
echo "💡 To rollback to V9 permanently:"
echo "   cp $V9_BACKUP $CURRENT_MODEL_EXTERNAL"
echo "   cp $V9_BACKUP $CURRENT_MODEL_INTERNAL"
echo ""
echo "📊 Model Comparison:"
echo "   Version: V10 (Enriched Assembly + Deep Understanding)"
echo "   Dataset: 12,267 examples (37.6% assembly coverage)"
echo "   Epochs: 2"
echo "   Learning rate: 2e-4 (optimized)"
echo "   F16 size: $(du -h "$F16_OUTPUT" | cut -f1)"
echo "   Q6 size:  $(du -h "$Q6_OUTPUT" | cut -f1)"
echo "   Compression: ~60%"
echo ""
echo "✨ V10 New Features (vs V9):"
echo "   • Enriched dataset: merged ALL available data (155MB + 73MB)"
echo "   • 4,616 assembly Q&A pairs (37.6% of dataset)"
echo "   • Cleaned assembly output (removed compiler metadata)"
echo "   • Optimized learning rate (2e-4 for deep understanding)"
echo "   • Better regularization (weight decay 0.05)"
echo "   • Comprehensive coverage: concepts + assembly + edge cases"
echo ""
echo "📊 Default model location: $CURRENT_MODEL_INTERNAL"
echo "   External drive (primary): $CURRENT_MODEL_EXTERNAL"
echo ""
