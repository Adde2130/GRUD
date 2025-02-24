#!/usr/bin/env bash

IMG_FILE="${HOME}/dummy1.img"
MOUNT_POINT=""

if [ ! -f  "IMG_FILE" ]; then
	dd if=/dev/zero of="$IMG_FILE" bs=1M count=500 status=progress
	mkfs.vfat "$IMG_FILE"
fi 

LOOP_DEVICE=$(udisksctl loop-setup -f "$IMG_FILE" | awk '{print $NF}' | tr -d '.')
sleep 2  # Wait for device to initialize

LOOP_NAME=$(basename "$LOOP_DEVICE")
echo 1 | sudo tee "/sys/block/$LOOP_NAME/removable" >/dev/null

# Mount the loop device
MOUNT_INFO=$(udisksctl mount -b "$LOOP_DEVICE")
MOUNT_POINT=$(echo "$MOUNT_INFO" | awk '{print $4}')

echo "Fake USB mounted at: $MOUNT_POINT"
