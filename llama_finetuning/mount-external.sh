#!/bin/bash
# Mount external hard drive with models

MOUNT_POINT="/mnt/external"
DRIVE_LABEL="nitzanfamily"

# Check if already mounted
if mountpoint -q "$MOUNT_POINT"; then
    echo "✓ External drive already mounted at $MOUNT_POINT"
    ls -lh "$MOUNT_POINT/models/" 2>/dev/null && echo "Models directory accessible"
    exit 0
fi

# Find device by label
DEVICE=$(lsblk -rno NAME,LABEL | grep "$DRIVE_LABEL" | awk '{print "/dev/"$1}')

if [ -z "$DEVICE" ]; then
    echo "✗ Drive with label '$DRIVE_LABEL' not found"
    echo ""
    echo "Available drives:"
    lsblk -f | grep -E "sd"
    echo ""
    echo "Is your external hard drive plugged in?"
    exit 1
fi

echo "Found drive: $DEVICE"

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Creating mount point $MOUNT_POINT..."
    sudo mkdir -p "$MOUNT_POINT"
fi

# Mount the drive
echo "Mounting $DEVICE to $MOUNT_POINT..."
sudo mount -t ntfs-3g "$DEVICE" "$MOUNT_POINT"

if [ $? -eq 0 ]; then
    echo "✓ Successfully mounted external drive"
    echo "Models directory: $MOUNT_POINT/models/"
    ls -lh "$MOUNT_POINT/models/" 2>/dev/null || echo "Warning: models directory not found"
else
    echo "✗ Failed to mount drive"
    exit 1
fi
