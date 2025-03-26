# Dumb Scripts

A collection of simple, single-purpose scripts for various tasks.

## Scripts Included

*   **[documents_to_markdown_converter](./documents_to_markdown_converter/)**: Converts PDF documents (especially slides) to Markdown format using the Mistral API for OCR and content generation. Includes image extraction and batch processing.
*   **[download_selfhst_icons](./download_selfhst_icons/)**: Downloads all PNG icons (including light variants) listed on the `selfh.st/icons` page using Puppeteer and shell scripting.
*   **[firefox_sidebery_snapshot_manager](./firefox_sidebery_snapshot_manager/)**: Manages snapshots created by the Firefox Sidebery extension by automatically deleting the oldest ones beyond a specified limit.
*   **[image_optimization_for_websites](./image_optimization_for_websites/)**: Optimizes and converts images to AVIF or WebP formats, resizing them and adjusting quality based on image dimensions.
*   **[minecraft_log_manager](./minecraft_log_manager/)**: Manages log files for multiple Minecraft server instances, keeping a configurable number of recent logs and rotating large `screen.log` files.
*   **[stt_from_audio_or_video](./stt_from_audio_or_video/)**: Transcribes audio and video files using Groq's Whisper API, automatically optimizing large or unsupported files with ffmpeg.
*   **[glance_widgets](./glance_widgets/)**: Custom widgets for the [Glance](https://github.com/glanceapp/glance) system monitoring tool (e.g., Unraid stats, Jellyfin streams, OpenRouter credits).
*   **[galaxybook_kb_brightness_sync](./galaxybook_kb_brightness_sync/)**: Adjusts keyboard backlight brightness based on display brightness percentage, primarily for Samsung Galaxy Book devices using the `samsung-galaxybook::kbd_backlight` device provided by the [samsung-galaxybook-extras](https://github.com/joshuagrisham/samsung-galaxybook-extras) kernel module via `brightnessctl`.

Each directory contains the specific script(s) and its own detailed README file with setup and usage instructions.