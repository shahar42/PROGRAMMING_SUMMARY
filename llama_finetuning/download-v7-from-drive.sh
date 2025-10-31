#!/bin/bash

# Download V7 model from Google Drive to external drive
# Usage: ./download-v7-from-drive.sh [FOLDER_ID]

set -e

# Get folder ID from argument or prompt
if [ -n "$1" ]; then
    FOLDER_ID="$1"
else
    echo "=================================================="
    echo "V7 Model Download (Real Compiler Facts)"
    echo "=================================================="
    echo ""
    echo "Get the Google Drive folder ID from your Colab upload:"
    echo "1. Upload final_model_merged to Drive"
    echo "2. Right-click folder → Get link"
    echo "3. Extract ID from: https://drive.google.com/drive/folders/FOLDER_ID"
    echo ""
    read -p "Enter Folder ID: " FOLDER_ID
fi

OUTPUT_DIR="/mnt/external/models/v7_model_merged"

echo ""
echo "=================================================="
echo "Downloading V7 Model from Google Drive"
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
echo "(~16GB, may take 10-20 minutes depending on connection)"
echo ""

gdown --folder "$FOLDER_ID" -O "$OUTPUT_DIR" --remaining-ok

echo ""
echo "=================================================="
echo "✅ Download complete!"
echo "=================================================="
echo "📂 Files saved to: $OUTPUT_DIR"
echo ""
echo "Checking downloaded files:"
ls -lh "$OUTPUT_DIR"
echo ""
echo "Next step: Run ./deploy-v7-model.sh"
echo "=================================================="
