# Samsung Galaxy Book Keyboard Brightness Sync

This script automatically adjusts the keyboard backlight level on Samsung Galaxy Book devices based on the current display brightness percentage. It relies on the `samsung-galaxybook::kbd_backlight` device created by the [samsung-galaxybook-extras](https://github.com/joshuagrisham/samsung-galaxybook-extras) kernel module and uses `brightnessctl` for control.

## Features

-   Reads the current display brightness and calculates its percentage relative to the maximum brightness.
-   Sets the keyboard backlight level based on predefined thresholds of display brightness percentage.
-   Uses `brightnessctl` to control the keyboard backlight via the `samsung-galaxybook::kbd_backlight` device (or a specified alternative).

## Requirements

-   Bash
-   A Samsung Galaxy Book (or compatible device) with the [samsung-galaxybook-extras](https://github.com/joshuagrisham/samsung-galaxybook-extras) kernel module installed and loaded. This module provides the necessary `samsung-galaxybook::kbd_backlight` device.
-   `brightnessctl`: A utility to control device brightness. Install it using your package manager (e.g., `sudo apt install brightnessctl` or `sudo pacman -S brightnessctl`).
-   A system with controllable display backlight (usually found under `/sys/class/backlight/`).

## Usage

```bash
./galaxybook_kb_brightness_sync.sh [keyboard_device]
```

**Arguments:**

-   `[keyboard_device]`: (Optional) The name of the keyboard backlight device as recognized by `brightnessctl`. If omitted, it defaults to `"samsung-galaxybook::kbd_backlight"`. You might need to specify a different device if your setup differs or if you adapt this script for non-Galaxy Book hardware.

**Finding your Keyboard Device:**

You can list available devices using:

```bash
brightnessctl -l
```

Look for a device related to keyboard backlight. For Samsung Galaxy Books with the required module, it should be `samsung-galaxybook::kbd_backlight`. Other examples might include `tpacpi::kbd_backlight` or `asus::kbd_backlight`.

**Example (using the default device):**

```bash
./galaxybook_kb_brightness_sync.sh
```

**Example (using a custom device):**

```bash
./galaxybook_kb_brightness_sync.sh asus::kbd_backlight
```

## Logic

The script sets the keyboard backlight level (`KB_LEVEL`) based on the display brightness percentage (`BRIGHTNESS_PERCENT`):

-   `BRIGHTNESS_PERCENT < 5%`: `KB_LEVEL = 3` (Highest keyboard brightness)
-   `5% <= BRIGHTNESS_PERCENT < 45%`: `KB_LEVEL = 2`
-   `45% <= BRIGHTNESS_PERCENT < 90%`: `KB_LEVEL = 1`
-   `BRIGHTNESS_PERCENT >= 90%`: `KB_LEVEL = 0` (Keyboard backlight off)

*Note: The specific levels (0, 1, 2, 3) correspond to the levels supported by the `samsung-galaxybook-extras` module.*

## Automation

This script is most useful when run automatically whenever the display brightness changes. You can achieve this using tools like `udev` rules.

**Example Udev Rule:**

Create a file like `/etc/udev/rules.d/99-galaxybook-keyboard-backlight-sync.rules` with the following content (adjust paths and user as needed):

```udev
ACTION=="change", SUBSYSTEM=="backlight", KERNEL=="acpi_video0", ENV{DISPLAY}=":0", ENV{XAUTHORITY}="/home/your_user/.Xauthority", RUN+="/usr/bin/su your_user -c '/path/to/repo/galaxybook_kb_brightness_sync/galaxybook_kb_brightness_sync.sh'"
```

-   Replace `acpi_video0` with your actual display backlight device name (check `/sys/class/backlight/`).
-   Replace `your_user` with your username.
-   Replace `/path/to/repo/...` with the full path to the script.
-   If you need to specify a non-default keyboard device, add it as an argument to the script path in the `RUN` command.

After creating the rule, reload udev rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Ensure the script has execute permissions (`chmod +x galaxybook_kb_brightness_sync.sh`).