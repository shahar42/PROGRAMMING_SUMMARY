#!/bin/bash
# Deploy V6 Enhanced Model - Complete Pipeline
# Run this after training completes on Colab

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP="$SCRIPT_DIR/llama.cpp"
MODELS_DIR="/mnt/external/models"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      Feather V6 Enhanced Model Deployment Pipeline            ║"
echo "║      (Assembly-Level C/C++ Programming Assistant)             ║"
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

# Step 3: Download V6 model from Google Drive
echo "📥 Step 3: Downloading V6 Enhanced model from Google Drive..."
echo "──────────────────────────────────────────────────────────────────"

V6_MODEL_DIR="$MODELS_DIR/v6_model_merged"

if [ ! -d "$V6_MODEL_DIR" ] || [ -z "$(ls -A "$V6_MODEL_DIR" 2>/dev/null)" ]; then
    echo "Model not found locally, downloading from Google Drive..."

    # Check if gdown is available
    if ! command -v gdown &> /dev/null; then
        echo "❌ gdown not installed"
        echo ""
        echo "Install with: pip install gdown"
        echo ""
        echo "Or download manually from Drive to: $V6_MODEL_DIR"
        exit 1
    fi

    # Google Drive folder ID from the link
    # https://drive.google.com/drive/u/0/folders/FOLDER_ID
    read -p "Enter Google Drive folder ID for final_model_merged: " FOLDER_ID

    if [ -z "$FOLDER_ID" ]; then
        echo "❌ No folder ID provided"
        exit 1
    fi

    # Create directory
    mkdir -p "$V6_MODEL_DIR"

    # Download from Google Drive using gdown
    echo "Downloading (this may take several minutes, ~16GB)..."
    gdown --folder "https://drive.google.com/drive/folders/$FOLDER_ID" \
        -O "$V6_MODEL_DIR" --remaining-ok

    if [ $? -ne 0 ]; then
        echo "❌ Download failed"
        echo ""
        echo "Manual download:"
        echo "1. Go to: https://drive.google.com/drive/folders/$FOLDER_ID"
        echo "2. Download entire folder"
        echo "3. Extract to: $V6_MODEL_DIR"
        exit 1
    fi
else
    echo "✅ V6 model already downloaded"
fi

if [ ! -d "$V6_MODEL_DIR" ] || [ -z "$(ls -A "$V6_MODEL_DIR")" ]; then
    echo "❌ Model directory empty or missing"
    exit 1
fi

echo "✅ V6 model ready at: $V6_MODEL_DIR"
echo ""

# Step 4: Convert to GGUF F16
echo "🔄 Step 4: Converting to GGUF F16..."
echo "──────────────────────────────────────────────────────────────────"

F16_OUTPUT="$MODELS_DIR/cpp-instructor-v6-f16.gguf"

if [ -f "$F16_OUTPUT" ]; then
    echo "⚠️  F16 file already exists: $F16_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing F16 file..."
    else
        rm "$F16_OUTPUT"
        python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V6_MODEL_DIR" \
            --outfile "$F16_OUTPUT" \
            --outtype f16
    fi
else
    python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V6_MODEL_DIR" \
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

Q5_OUTPUT="$MODELS_DIR/cpp-instructor-v6-q5.gguf"

if [ -f "$Q5_OUTPUT" ]; then
    echo "⚠️  Q5 file already exists: $Q5_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing Q5 file..."
    else
        rm "$Q5_OUTPUT"
        "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q5_OUTPUT" Q5_K_M
    fi
else
    "$LLAMA_CPP/build/bin/llama-quantize" "$F16_OUTPUT" "$Q5_OUTPUT" Q5_K_M
fi

if [ ! -f "$Q5_OUTPUT" ]; then
    echo "❌ Q5 quantization failed"
    exit 1
fi

echo "✅ Q5_K_M quantized: $Q5_OUTPUT"
echo "📊 Size: $(du -h "$Q5_OUTPUT" | cut -f1)"
echo ""

# Step 6: Verify V5 backup exists
echo "💾 Step 6: Verifying V5 backup..."
echo "──────────────────────────────────────────────────────────────────"

V5_BACKUP="$MODELS_DIR/cpp-instructor-v5-q5.gguf"

if [ -f "$V5_BACKUP" ]; then
    echo "✅ V5 backup exists: $V5_BACKUP"
    echo "📊 Size: $(du -h "$V5_BACKUP" | cut -f1)"
else
    echo "⚠️  V5 backup not found!"
    echo "   Expected: $V5_BACKUP"
    echo "   This backup should have been created before running deployment."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi
echo ""

# Step 7: Deploy V6 to external drive
echo "📦 Step 7: Deploying V6 Enhanced to external drive..."
echo "──────────────────────────────────────────────────────────────────"

V6_DEPLOYED="$MODELS_DIR/cpp-instructor-q5.gguf"

echo "Copying to: $V6_DEPLOYED"
cp "$Q5_OUTPUT" "$V6_DEPLOYED"

if [ ! -f "$V6_DEPLOYED" ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ V6 Enhanced model deployed"
echo "📊 Size: $(du -h "$V6_DEPLOYED" | cut -f1)"
echo ""

# Step 8: Test deployment
echo "🧪 Step 8: Testing V6 Enhanced deployment..."
echo "──────────────────────────────────────────────────────────────────"

if command -v feather &> /dev/null; then
    echo "Testing assembly knowledge..."
    TEST_OUTPUT=$(feather "What assembly does x++ generate?" 2>/dev/null | head -20)

    if [ -z "$TEST_OUTPUT" ]; then
        echo "⚠️  Model loaded but produced no output"
    else
        echo "✅ V6 Enhanced model responds successfully"
        echo ""
        echo "Sample output:"
        echo "$TEST_OUTPUT"
    fi
else
    echo "⚠️  'feather' command not found, skipping test"
    echo "   (Model is deployed, test manually)"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              V6 ENHANCED DEPLOYMENT COMPLETE!                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Deployment Summary:"
echo "   V6 Enhanced: $V6_DEPLOYED"
echo "   V5 Backup:   $V5_BACKUP"
echo "   Local F16:   $F16_OUTPUT"
echo "   Local Q5:    $Q5_OUTPUT"
echo ""
echo "🎯 Test V6 Enhanced Assembly Knowledge:"
echo "   feather \"What assembly does x++ generate?\""
echo "   feather \"Show memory layout of struct { char a; int b; }\""
echo "   feather \"What registers are used for function arguments in x86-64?\""
echo ""
echo "🔄 To compare with V5:"
echo "   compare-models \"Explain virtual functions\""
echo ""
echo "💡 To rollback to V5:"
echo "   cp $V5_BACKUP $V6_DEPLOYED"
echo ""
echo "✨ V6 Enhanced Features:"
echo "   • Concrete assembly code (gcc -S output)"
echo "   • Register usage (%rdi, %rax, etc.)"
echo "   • Memory layouts with byte offsets"
echo "   • Platform-specific details (x86-64, System V ABI)"
echo ""
