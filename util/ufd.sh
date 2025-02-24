#!/bin/bash
IMG_FILE="${HOME}/dummy1.img"
LOOP_DEVICE=$(losetup -j "$IMG_FILE" | awk '{print $1}' | sed 's/://')

if [ -n "$LOOP_DEVICE" ]; then
	udisksctl unmount -b "$LOOP_DEVICE"
	udisksctl loop-delete -b "$LOOP_DEVICE"
	echo "Fake USB unmounted and removed."
else
	echo "No fake USB device found."
fi
