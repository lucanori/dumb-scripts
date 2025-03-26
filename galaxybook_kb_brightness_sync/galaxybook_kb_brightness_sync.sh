#!/bin/bash

# Default keyboard backlight device
DEFAULT_KB_DEVICE="samsung-galaxybook::kbd_backlight"
KB_DEVICE="${1:-$DEFAULT_KB_DEVICE}"

# Identify the display backlight interface
BACKLIGHT_DIR=$(find /sys/class/backlight -mindepth 1 -maxdepth 1 -type l | head -n 1)

if [ -z "$BACKLIGHT_DIR" ]; then
    echo "Error: No display backlight interface found in /sys/class/backlight." >&2
    exit 1
fi

# Read current brightness and maximum brightness
if [ ! -f "$BACKLIGHT_DIR/brightness" ] || [ ! -f "$BACKLIGHT_DIR/max_brightness" ]; then
    echo "Error: Cannot read brightness values from $BACKLIGHT_DIR." >&2
    exit 1
fi
CURRENT_BRIGHTNESS=$(cat "$BACKLIGHT_DIR/brightness")
MAX_BRIGHTNESS=$(cat "$BACKLIGHT_DIR/max_brightness")

# Check if brightness values are valid numbers
if ! [[ "$CURRENT_BRIGHTNESS" =~ ^[0-9]+$ ]] || ! [[ "$MAX_BRIGHTNESS" =~ ^[0-9]+$ ]] || [ "$MAX_BRIGHTNESS" -eq 0 ]; then
    echo "Error: Invalid brightness values found (Current: $CURRENT_BRIGHTNESS, Max: $MAX_BRIGHTNESS)." >&2
    exit 1
fi


# Calculate brightness percentage
BRIGHTNESS_PERCENT=$(( 100 * CURRENT_BRIGHTNESS / MAX_BRIGHTNESS ))

# Determine keyboard backlight level based on brightness percentage
if [ "$BRIGHTNESS_PERCENT" -lt 5 ]; then
    KB_LEVEL=3
elif [ "$BRIGHTNESS_PERCENT" -lt 45 ]; then
    KB_LEVEL=2
elif [ "$BRIGHTNESS_PERCENT" -lt 90 ]; then
    KB_LEVEL=1
else
    KB_LEVEL=0
fi

# Set the keyboard backlight using brightnessctl
if ! command -v brightnessctl &> /dev/null; then
    echo "Error: brightnessctl command not found. Please install it." >&2
    exit 1
fi

brightnessctl -q -d "$KB_DEVICE" set "$KB_LEVEL"
if [ $? -ne 0 ]; then
    echo "Error: Failed to set keyboard backlight level for device '$KB_DEVICE'." >&2
    exit 1
fi

exit 0
