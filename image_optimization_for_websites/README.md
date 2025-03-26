# Image Processor

A Python script for optimizing and converting images with diagonal-based quality adjustment.

## Features

- Resize images while maintaining aspect ratio
- Convert to AVIF or WebP formats
- Smart quality adjustment based on image diagonal:
  - Small images (< 1470px diagonal): 95% quality
  - Larger images (≥ 1470px diagonal): 80% quality
- Process single images or entire directories
- Recursive directory processing option
- Detailed output with size reduction statistics

## Requirements

- Python 3.6+
- Pillow
- pillow-avif-plugin (for AVIF support)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>/image_optimization_for_websites
    ```
2.  **Install dependencies:**
    It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

## Usage

### Basic Usage

```bash
# Process a single image
python image_processor.py input.jpg output.avif

# Process a directory of images
python image_processor.py input_directory/ output_directory/ 
```

### Advanced Options

```bash
# Set custom max dimension (default: 1200px)
python image_processor.py input.jpg output.avif --max-dimension 1600

# Use WebP format instead of AVIF
python image_processor.py input.jpg output.webp --format WEBP

# Set custom diagonal threshold for quality adjustment (default: 1470px)
python image_processor.py input.jpg output.avif --threshold 2000

# Process directory recursively (including subdirectories)
python image_processor.py input_directory/ output_directory/ --recursive
```

## Examples

### Convert a single image to AVIF

```bash
python image_processor.py photos/vacation.jpg optimized/vacation.avif
```

### Process all images in a directory

```bash
python image_processor.py photos/ optimized/ --format AVIF --threshold 2000
```

### Process an entire photo collection recursively

```bash
python image_processor.py photo_collection/ optimized_collection/ --recursive --format AVIF
```

## How It Works

The script analyzes each image's diagonal (√(width² + height²)) before processing:

1. If the image diagonal is smaller than the threshold (default: 1470px, equivalent to a 1280×720 image), it uses 95% quality to preserve details
2. If the image diagonal is larger than the threshold, it uses 80% quality for better compression

This approach ensures small images maintain maximum quality while larger images benefit from better compression. Using the diagonal measurement instead of file size provides more consistent results across different image formats and content types.