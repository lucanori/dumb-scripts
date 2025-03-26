#!/usr/bin/env python3

import os
import sys
import math
from pathlib import Path
import argparse
from PIL import Image

# Check if pillow-avif-plugin is installed
try:
    from pillow_avif import AvifImagePlugin
except ImportError:
    print("Warning: pillow-avif-plugin not installed. AVIF support may be limited.")
    print("Install with: pip install pillow-avif-plugin")

def get_file_size_kb(file_path):
    """Get file size in kilobytes"""
    return os.path.getsize(file_path) / 1024

def calculate_diagonal(width, height):
    """Calculate the diagonal of an image in pixels using the Pythagorean theorem"""
    return math.sqrt(width**2 + height**2)

def optimize_image(input_path, output_path, max_dimension=1200, format='AVIF', diagonal_threshold=1470):
    """
    Optimize an image with diagonal-based quality adjustment:
    - If diagonal < threshold: use quality 95%
    - If diagonal >= threshold: use quality 80%
    """
    try:
        # Get original file size for reporting
        original_size_kb = get_file_size_kb(input_path)
        
        # Open the image to get its dimensions
        with Image.open(input_path) as img_for_size:
            width, height = img_for_size.size
            diagonal = calculate_diagonal(width, height)
        
        # Determine quality based on diagonal
        quality = 95 if diagonal < diagonal_threshold else 80
        
        with Image.open(input_path) as img:
            # Maintain aspect ratio
            img.thumbnail((max_dimension, max_dimension))
            
            save_kwargs = {
                'quality': quality
            }
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            if format.upper() == 'AVIF':
                img.save(output_path, 'AVIF', **save_kwargs)
            elif format.upper() == 'WEBP':
                img.save(output_path, 'WEBP', **save_kwargs)
            else:
                # Default to original format if not AVIF or WEBP
                img.save(output_path, **save_kwargs)
                
        # Get new file size for reporting
        new_size_kb = get_file_size_kb(output_path)
        reduction = (1 - (new_size_kb / original_size_kb)) * 100
        
        print(f"Processed: {os.path.basename(input_path)}")
        print(f"  Original: {original_size_kb:.2f} KB, Diagonal: {diagonal:.0f}px")
        print(f"  New: {new_size_kb:.2f} KB ({reduction:.1f}% reduction)")
        print(f"  Quality: {quality}%")
        
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def process_directory(input_dir, output_dir, max_dimension=1200, format='AVIF',
                     diagonal_threshold=1470, recursive=False):
    """Process all images in a directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    if recursive:
        image_files = [f for f in input_path.glob('**/*') if f.is_file() and f.suffix.lower() in image_extensions]
    else:
        image_files = [f for f in input_path.glob('*') if f.is_file() and f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
    
    print(f"Found {len(image_files)} images to process")
    
    success_count = 0
    for img_file in image_files:
        # Preserve directory structure for recursive processing
        if recursive:
            rel_path = img_file.relative_to(input_path)
            out_file = output_path / rel_path.with_suffix(f'.{format.lower()}')
            out_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_file = output_path / f"{img_file.stem}.{format.lower()}"
        
        if optimize_image(str(img_file), str(out_file), max_dimension, format, diagonal_threshold):
            success_count += 1
    
    print(f"\nProcessing complete: {success_count}/{len(image_files)} images successfully processed")

def main():
    parser = argparse.ArgumentParser(description='Optimize and convert images with diagonal-based quality adjustment')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('output', help='Output file or directory')
    parser.add_argument('--max-dimension', type=int, default=1200, help='Maximum dimension (width or height)')
    parser.add_argument('--format', choices=['AVIF', 'WEBP'], default='AVIF', help='Output format')
    parser.add_argument('--threshold', type=int, default=1470, help='Diagonal threshold in pixels for quality adjustment')
    parser.add_argument('--recursive', action='store_true', help='Process directories recursively')
    
    args = parser.parse_args()
    
    if os.path.isfile(args.input):
        # Process single file
        optimize_image(args.input, args.output, args.max_dimension, args.format, args.threshold)
    elif os.path.isdir(args.input):
        # Process directory
        process_directory(args.input, args.output, args.max_dimension, args.format,
                         args.threshold, args.recursive)
    else:
        print(f"Error: Input path '{args.input}' does not exist")
        sys.exit(1)

if __name__ == "__main__":
    main()