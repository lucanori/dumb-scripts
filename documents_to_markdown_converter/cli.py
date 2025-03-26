#!/usr/bin/env python3
import argparse
import os
from logging_setup import get_logger

logger = get_logger()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Convert PDF slides to markdown using Mistral OCR')
    parser.add_argument('--input', '-i', type=str, default='input', 
                        help='Input directory containing PDF files')
    parser.add_argument('--output', '-o', type=str, default='output',
                        help='Output directory for markdown files')
    parser.add_argument('--batch', '-b', action='store_true',
                        help='Use batch processing for multiple PDFs')
    parser.add_argument('--auto', '-a', action='store_true',
                        help='Automatically switch to batch processing if multiple PDFs need processing')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug logging')
    return parser.parse_args()

def validate_directories(input_dir, output_dir):
    try:
        if not os.path.exists(input_dir):
            os.makedirs(input_dir, exist_ok=True)
            logger.info(f"Created input directory: {input_dir}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        return True
    except PermissionError:
        logger.error("Permission denied when trying to create directories")
        return False
    except OSError as e:
        logger.error(f"Error creating directories: {e}")
        return False