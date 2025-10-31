#!/bin/bash

# Download V2 model from Google Drive to external drive
# Usage: ./download-v2-from-drive.sh

set -e

FOLDER_ID="12R6dcbZYIgx5YFjw83C-Kjra_LhoGXxP"
OUTPUT_DIR="/mnt/external/models/v2_model_merged"

echo "=================================================="
echo "Downloading V2 Model from Google Drive"
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
echo "Next step: Run ./deploy-v2-model.sh"
echo "=================================================="
