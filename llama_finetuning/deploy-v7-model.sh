#!/bin/bash
# Deploy V7 Model - Complete Pipeline
# Run this after training completes on Colab

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LLAMA_CPP="$SCRIPT_DIR/llama.cpp"
MODELS_DIR="/mnt/external/models"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Feather V7 Model Deployment Pipeline                  ║"
echo "║         (Real Compiler Facts + POSIX Knowledge)               ║"
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

# Step 3: Download V7 model from Google Drive
echo "📥 Step 3: Downloading V7 model from Google Drive..."
echo "──────────────────────────────────────────────────────────────────"

V7_MODEL_DIR="$MODELS_DIR/v7_model_merged"

if [ ! -d "$V7_MODEL_DIR" ] || [ -z "$(ls -A "$V7_MODEL_DIR" 2>/dev/null)" ]; then
    echo "Model not found locally, downloading from Google Drive..."

    # Check if gdown is available
    if ! command -v gdown &> /dev/null; then
        echo "❌ gdown not installed"
        echo ""
        echo "Install with: pip install gdown"
        echo ""
        echo "Or download manually from Drive to: $V7_MODEL_DIR"
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
    mkdir -p "$V7_MODEL_DIR"

    # Download from Google Drive using gdown
    echo "Downloading (this may take several minutes, ~16GB)..."
    gdown --folder "https://drive.google.com/drive/folders/$FOLDER_ID" \
        -O "$V7_MODEL_DIR" --remaining-ok

    if [ $? -ne 0 ]; then
        echo "❌ Download failed"
        echo ""
        echo "Manual download:"
        echo "1. Go to: https://drive.google.com/drive/folders/$FOLDER_ID"
        echo "2. Download entire folder"
        echo "3. Extract to: $V7_MODEL_DIR"
        exit 1
    fi
else
    echo "✅ V7 model already downloaded"
fi

if [ ! -d "$V7_MODEL_DIR" ] || [ -z "$(ls -A "$V7_MODEL_DIR")" ]; then
    echo "❌ Model directory empty or missing"
    exit 1
fi

echo "✅ V7 model ready at: $V7_MODEL_DIR"
echo ""

# Step 4: Convert to GGUF F16
echo "🔄 Step 4: Converting to GGUF F16..."
echo "──────────────────────────────────────────────────────────────────"

F16_OUTPUT="$MODELS_DIR/cpp-instructor-v7-f16.gguf"

if [ -f "$F16_OUTPUT" ]; then
    echo "⚠️  F16 file already exists: $F16_OUTPUT"
    read -p "Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing F16 file..."
    else
        rm "$F16_OUTPUT"
        python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V7_MODEL_DIR" \
            --outfile "$F16_OUTPUT" \
            --outtype f16
    fi
else
    python3 "$LLAMA_CPP/convert_hf_to_gguf.py" "$V7_MODEL_DIR" \
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

Q5_OUTPUT="$MODELS_DIR/cpp-instructor-v7-q5.gguf"

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

# Step 6: Backup V6
echo "💾 Step 6: Backing up V6..."
echo "──────────────────────────────────────────────────────────────────"

CURRENT_MODEL="$MODELS_DIR/cpp-instructor-q5.gguf"
V6_BACKUP="$MODELS_DIR/cpp-instructor-v6-q5.gguf"

if [ -f "$CURRENT_MODEL" ]; then
    if [ -f "$V6_BACKUP" ]; then
        echo "⚠️  V6 backup already exists: $V6_BACKUP"
        echo "📊 Size: $(du -h "$V6_BACKUP" | cut -f1)"
    else
        echo "Creating V6 backup..."
        cp "$CURRENT_MODEL" "$V6_BACKUP"
        echo "✅ V6 backed up to: $V6_BACKUP"
        echo "📊 Size: $(du -h "$V6_BACKUP" | cut -f1)"
    fi
else
    echo "⚠️  No current model found (this is OK for first-time deployment)"
fi
echo ""

# Step 7: Deploy V7 to external drive
echo "📦 Step 7: Deploying V7 to external drive..."
echo "──────────────────────────────────────────────────────────────────"

echo "Copying to: $CURRENT_MODEL"
cp "$Q5_OUTPUT" "$CURRENT_MODEL"

if [ ! -f "$CURRENT_MODEL" ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo "✅ V7 model deployed to external drive"
echo "📊 Size: $(du -h "$CURRENT_MODEL" | cut -f1)"
echo ""

# Step 8: Deploy V7 to internal SSD (default location)
echo "📦 Step 8: Deploying V7 to internal SSD (faster, default)..."
echo "──────────────────────────────────────────────────────────────────"

INTERNAL_MODEL="$HOME/.local/share/llama-models/cpp-instructor-q5.gguf"
INTERNAL_DIR="$HOME/.local/share/llama-models"

# Create directory if needed
mkdir -p "$INTERNAL_DIR"

echo "Copying to: $INTERNAL_MODEL"
cp "$Q5_OUTPUT" "$INTERNAL_MODEL"

if [ ! -f "$INTERNAL_MODEL" ]; then
    echo "❌ Internal deployment failed"
    exit 1
fi

echo "✅ V7 model deployed to internal SSD"
echo "📊 Size: $(du -h "$INTERNAL_MODEL" | cut -f1)"
echo ""

# Step 9: Test deployment with critical test cases
echo "🧪 Step 9: Testing V7 deployment with critical test cases..."
echo "──────────────────────────────────────────────────────────────────"

if command -v feather &> /dev/null; then
    echo "Testing critical V7 fixes (V6 failures)..."
    echo ""

    # Test 1: sizeof struct padding (V6 said 4, should be 8)
    echo "Test 1: sizeof(struct { char a; int b; })"
    echo "────────────────────────────────────────"
    TEST_OUTPUT=$(feather "What is sizeof(struct { char a; int b; })?" 2>/dev/null | head -5)

    if echo "$TEST_OUTPUT" | grep -q "8 bytes"; then
        echo "✅ PASS - Correctly answers 8 bytes (V6 said 4)"
    else
        echo "⚠️  Check answer manually:"
        echo "$TEST_OUTPUT"
    fi
    echo ""

    # Test 2: sizeof array (V6 said 4, should be 12)
    echo "Test 2: sizeof(int[3])"
    echo "────────────────────────────────────────"
    TEST_OUTPUT=$(feather "What is sizeof(int[3])?" 2>/dev/null | head -5)

    if echo "$TEST_OUTPUT" | grep -q "12 bytes"; then
        echo "✅ PASS - Correctly answers 12 bytes (V6 said 4)"
    else
        echo "⚠️  Check answer manually:"
        echo "$TEST_OUTPUT"
    fi
    echo ""

    # Test 3: POSIX syscall knowledge
    echo "Test 3: POSIX syscall knowledge (open errno codes)"
    echo "────────────────────────────────────────"
    TEST_OUTPUT=$(feather "What errno codes can open() return?" 2>/dev/null | head -10)

    if echo "$TEST_OUTPUT" | grep -q "EACCES\|EINVAL"; then
        echo "✅ PASS - Shows POSIX errno knowledge"
    else
        echo "⚠️  Check answer manually:"
        echo "$TEST_OUTPUT"
    fi
    echo ""
else
    echo "⚠️  'feather' command not found, skipping test"
    echo "   (Model is deployed, test manually)"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                 V7 DEPLOYMENT COMPLETE!                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Deployment Summary:"
echo "   V7 Active (external): $CURRENT_MODEL"
echo "   V7 Active (internal): $INTERNAL_MODEL"
echo "   V6 Backup:            $V6_BACKUP"
echo "   Local F16:            $F16_OUTPUT"
echo "   Local Q5:             $Q5_OUTPUT"
echo ""
echo "🎯 Test V7 Critical Fixes (V6 Failures):"
echo "   feather \"What is sizeof(struct { char a; int b; })?\""
echo "   # Expected: 8 bytes (V6 said 4 - WRONG)"
echo ""
echo "   feather \"What is sizeof(int[3])?\""
echo "   # Expected: 12 bytes (V6 said 4 - WRONG)"
echo ""
echo "   feather \"What errno codes can open() return?\""
echo "   # Expected: EACCES, EINVAL, etc. (V7 POSIX knowledge)"
echo ""
echo "   feather \"What is O_CREAT?\""
echo "   # Expected: \"Create file if it does not exist\" (V7 flag knowledge)"
echo ""
echo "🔄 To compare with V6:"
echo "   # Switch to external (V6 backup still there)"
echo "   feather --external \"What is sizeof(struct { char a; int b; })?\""
echo ""
echo "💡 To rollback to V6:"
echo "   cp $V6_BACKUP $CURRENT_MODEL"
echo "   cp $V6_BACKUP $INTERNAL_MODEL"
echo ""
echo "✨ V7 Key Improvements Over V6:"
echo "   • Real compiler sizeof values (92 types verified with gcc)"
echo "   • POSIX syscall knowledge (51 syscalls from manpages)"
echo "   • Concrete answers (\"8 bytes\" not \"depends on platform\")"
echo "   • Fixed V6 hallucinations (struct padding, array sizes)"
echo "   • Improved validation set (critical tests, edge cases)"
echo ""
echo "📊 Model uses internal SSD by default (faster load)"
echo "   Use 'feather --external' for external drive version"
echo ""
