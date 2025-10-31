#!/bin/bash

# Download V9 model from Google Drive to external drive
# Usage: ./download-v9-from-drive.sh [FOLDER_ID]

set -e

# Get folder ID from argument or prompt
if [ -n "$1" ]; then
    FOLDER_ID="$1"
else
    echo "=================================================="
    echo "V9 Model Download (Code + Assembly)"
    echo "=================================================="
    echo ""
    echo "Get the Google Drive folder ID from your Colab upload:"
    echo "1. In Colab, after merge completes"
    echo "2. Go to Google Drive"
    echo "3. Navigate to: fine_tuning_llama_v9_clean/model_v9_merged"
    echo "4. Right-click folder → Get link"
    echo "5. Extract ID from: https://drive.google.com/drive/folders/FOLDER_ID"
    echo ""
    read -p "Enter Folder ID: " FOLDER_ID
fi

OUTPUT_DIR="/mnt/external/models/v9_model_merged"

echo ""
echo "=================================================="
echo "Downloading V9 Model from Google Drive"
echo "=================================================="

# Check if external drive is mounted
if [ ! -d "/mnt/external" ]; then
    echo "❌ External drive not mounted!"
    echo "Run: ./mount-external.sh"
    exit 1
fi

# Create output directory
echo "📁 Creating output directory: $OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Check if gdown is installed
if ! command -v gdown &> /dev/null; then
    echo "❌ gdown not installed!"
    echo "Installing gdown..."
    pip install gdown
fi

# Download entire folder
echo "⬇️  Downloading entire folder to $OUTPUT_DIR..."
echo "This will download all files including tokenizer files"
echo "(~16GB, may take 10-30 minutes depending on connection)"
echo ""

gdown --folder "$FOLDER_ID" -O "$OUTPUT_DIR" --remaining-ok

echo ""
echo "=================================================="
echo "✅ Download complete!"
echo "=================================================="
echo "📂 Files saved to: $OUTPUT_DIR"
echo ""
echo "Checking downloaded files:"
ls -lh "$OUTPUT_DIR" | head -10
echo ""
echo "Expected files:"
echo "  ✓ config.json"
echo "  ✓ model.safetensors (~16GB)"
echo "  ✓ tokenizer.json"
echo "  ✓ tokenizer.model"
echo "  ✓ tokenizer_config.json"
echo "  ✓ special_tokens_map.json"
echo "  ✓ generation_config.json"
echo ""
echo "Next step: Run ./deploy-v9-model.sh"
echo "=================================================="
