#!/bin/bash
# Deploy V2 Model - Complete Pipeline
# Run this after training completes on Colab

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP="$SCRIPT_DIR/llama.cpp"
MODELS_DIR="/mnt/external/models"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Feather V2 Model Deployment Pipeline                  ║"
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

# Step 3: Download V2 model from Google Drive
echo "📥 Step 3: Downloading V2 model from Google Drive..."
echo "──────────────────────────────────────────────────────────────────"

V4_MODEL_DIR="$MODELS_DIR/v4_model_merged"

if [ ! -d "$V4_MODEL_DIR" ] || [ -z "$(ls -A "$V4_MODEL_DIR" 2>/dev/null)" ]; then
    echo "Model not found locally, downloading from Google Drive..."

    # Check if gdown is available
    if ! command -v gdown &> /dev/null; then
        echo "❌ gdown not installed"
        echo ""
        echo "Install with: pip install gdown"
        echo ""
        echo "Or download manually from Drive to: $V2_MODEL_DIR"
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
    mkdir -p "$V4_MODEL_DIR"

    # Download from Google Drive using gdown
    echo "Downloading (this may take several minutes, ~16GB)..."
    gdown --folder "https://drive.google.com/drive/folders/$FOLDER_ID" \
        -O "$V4_MODEL_DIR" --remaining-ok

    if [ $? -ne 0 ]; then
        echo "❌ Download failed"
        echo ""
        echo "Manual download:"
        echo "1. Go to: https://drive.google.com/drive/folders/$FOLDER_ID"
        echo "2. Download entire folder"
        echo "3. Extract to: $V4_MODEL_DIR"
        exit 1
    fi
else
    echo "✅ V4 model already downloaded"
fi

if [ ! -d "$V4_MODEL_DIR" ] || [ -z "$(ls -A "$V4_MODEL_DIR")" ]; then
    echo "❌ Model directory empty or missing"
    exit 1
fi

echo "✅ V4 model ready at: $V4_MODEL_DIR"
echo ""

# Step 4: Convert to GGUF F16
echo "🔄 Step 4: Converting to GGUF F16..."
echo "──────────────────────────────────────────────────────────────────"

F16_OUTPUT="$MODELS_DIR/cpp-instructor-v4-f16.gguf"

if [ -f "$F16_OUTPUT" ]; then
    echo "⚠️  F16 file already exists: $F16_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing F16 file..."
    else
        rm "$F16_OUTPUT"
        python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V4_MODEL_DIR" \
            --outfile "$F16_OUTPUT" \
            --outtype f16
    fi
else
    python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V4_MODEL_DIR" \
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

Q5_OUTPUT="$MODELS_DIR/cpp-instructor-v4-q5.gguf"

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

# Step 6: Backup V2 model
echo "💾 Step 6: Backing up V2 model..."
echo "──────────────────────────────────────────────────────────────────"

CURRENT_MODEL="$MODELS_DIR/cpp-instructor-q5.gguf"
V2_BACKUP="$MODELS_DIR/cpp-instructor-v2-q5.gguf"

if [ -f "$CURRENT_MODEL" ]; then
    if [ -f "$V2_BACKUP" ]; then
        echo "⚠️  V2 backup already exists, skipping..."
    else
        echo "Creating backup: $V2_BACKUP"
        cp "$CURRENT_MODEL" "$V2_BACKUP"
        echo "✅ V2 model backed up"
    fi
else
    echo "⚠️  Current model not found (first time setup?)"
fi
echo ""

# Step 7: Copy V4 to external drive
echo "📦 Step 7: Deploying V4 to external drive..."
echo "──────────────────────────────────────────────────────────────────"

V4_DEPLOYED="$MODELS_DIR/cpp-instructor-q5.gguf"

echo "Copying to: $V4_DEPLOYED"
cp "$Q5_OUTPUT" "$V4_DEPLOYED"

if [ ! -f "$V4_DEPLOYED" ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ V4 model deployed"
echo "📊 Size: $(du -h "$V4_DEPLOYED" | cut -f1)"
echo ""

# Step 8: Test deployment
echo "🧪 Step 8: Testing deployment..."
echo "──────────────────────────────────────────────────────────────────"

if command -v feather &> /dev/null; then
    echo "Testing with simple question..."
    TEST_OUTPUT=$(feather "What is RAII in one sentence?" 2>/dev/null | head -20)

    if [ -z "$TEST_OUTPUT" ]; then
        echo "⚠️  Model loaded but produced no output"
    else
        echo "✅ Model responds successfully"
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
echo "║                    DEPLOYMENT COMPLETE!                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Deployment Summary:"
echo "   V4 Model: $V4_DEPLOYED"
echo "   V2 Backup: $V2_BACKUP"
echo "   Local F16: $F16_OUTPUT"
echo "   Local Q5: $Q5_OUTPUT"
echo ""
echo "🎯 Next Steps:"
echo "   1. Test: feather \"How does the compiler implement virtual functions?\""
echo "   2. Interactive: feather"
echo "   3. Compare: compare-models \"What is RAII?\""
echo ""
echo "💡 To rollback to V2:"
echo "   cp $V2_BACKUP $V4_DEPLOYED"
echo ""
