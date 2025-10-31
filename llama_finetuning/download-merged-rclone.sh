#!/bin/bash

# Download merged V4 model using rclone (bypasses rate limits)
# Usage: ./download-merged-rclone.sh

set -e

OUTPUT_DIR="/mnt/external/models/v4_model_merged"

echo "=================================================="
echo "Downloading Merged V4 Model with rclone"
echo "=================================================="

# Check external drive
if [ ! -d "/mnt/external" ]; then
    echo "❌ External drive not mounted!"
    echo "Run: ./mount-external.sh"
    exit 1
fi

# Clean old files
if [ -d "$OUTPUT_DIR" ]; then
    echo "🗑️  Cleaning old files..."
    rm -rf "$OUTPUT_DIR"
fi

mkdir -p "$OUTPUT_DIR"

echo "⬇️  Downloading with rclone (~15GB)..."
echo "This bypasses Google Drive rate limits"
echo ""

# Use rclone to download entire folder
rclone copy "gdrive:fine_tuning_llama_v4/final_model_merged/" "$OUTPUT_DIR" \
    --progress \
    --transfers 4 \
    --checkers 8 \
    -v

echo ""
echo "=================================================="
echo "✅ Download complete!"
echo "=================================================="
echo "📂 Files:"
ls -lh "$OUTPUT_DIR"
echo ""
echo "Next: Run ./deploy-v2-model.sh"
echo "=================================================="
