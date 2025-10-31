#!/bin/bash

set -e

echo "=================================================="
echo "Downloading Missing V6 Model Files"
echo "=================================================="
echo ""

OUTPUT_DIR="/mnt/external/models/v6_model_merged"

# File IDs from Google Drive links
FILE_ID_2="1sqzC04KcliL-RrdrrMgNrWq73a1vl0QH"
FILE_ID_3="1oF-nQEyNNPsagXeBcVBwDVk_r1-KsdWG"

echo "📁 Output directory: $OUTPUT_DIR"
echo ""

# Download model-00002-of-00004.safetensors
echo "⬇️  Downloading model-00002-of-00004.safetensors..."
gdown "https://drive.google.com/uc?id=$FILE_ID_2" -O "$OUTPUT_DIR/model-00002-of-00004.safetensors"
echo "✅ model-00002-of-00004.safetensors complete"
echo ""

# Download model-00003-of-00004.safetensors
echo "⬇️  Downloading model-00003-of-00004.safetensors..."
gdown "https://drive.google.com/uc?id=$FILE_ID_3" -O "$OUTPUT_DIR/model-00003-of-00004.safetensors"
echo "✅ model-00003-of-00004.safetensors complete"
echo ""

echo "=================================================="
echo "✅ All missing files downloaded!"
echo "=================================================="
echo ""
echo "Verifying complete file list:"
ls -lh "$OUTPUT_DIR"/model-*.safetensors | awk '{print $9, $5}'
echo ""
echo "Expected 4 model files total. Ready for deployment!"
