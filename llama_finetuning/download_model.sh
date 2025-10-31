#!/bin/bash
# Download merged model from Google Drive to external drive

sudo mkdir -p /mnt/external/models
sudo chown $USER:$USER /mnt/external/models

echo "Downloading model (~16GB, takes 10-30 minutes)..."
gdown --folder https://drive.google.com/drive/folders/1sx6GdYPDBStJFdPrHBQyDZub3i1it4Sp -O /mnt/external/models/cpp-instructor

echo ""
echo "✅ Download complete!"
echo "📍 Location: /mnt/external/models/cpp-instructor"
echo ""
echo "Next: python cpp_instructor_simple.py --model /mnt/external/models/cpp-instructor"
