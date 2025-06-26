#!/usr/bin/env python3
import os
import logging
from mistralai import Mistral
from config import load_config
from logging_setup import setup_logging, get_logger
from cli import parse_arguments, validate_directories
from document_processing import process_single_file, process_batch_files
from utils import get_file_status, get_supported_files
from md_creation import process_json_file

def main():
    args = parse_arguments()
    
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logging(log_level)
    
    input_dir = args.input
    output_dir = args.output
    
    if not validate_directories(input_dir, output_dir):
        return
    
    try:
        config = load_config()
    except ValueError as e:
        logger.error(str(e))
        return
    
    client = Mistral(api_key=config["api_key"])
    
    supported_files = get_supported_files(input_dir)
    
    if not supported_files:
        logger.error(f"No supported files found in {input_dir}")
        logger.info("Supported formats: PDF, PPTX, DOCX, PNG, JPEG, AVIF")
        return
        
    logger.info(f"Found {len(supported_files)} supported files to process")
    
    use_batch = args.batch
    files_to_process = []
    json_ready_files = []
    
    for filename in supported_files:
        file_path = os.path.join(input_dir, filename)
        status = get_file_status(file_path, output_dir)
        
        if status == "needs_processing":
            files_to_process.append(filename)
        elif status == "json_ready":
            json_ready_files.append(filename)
    
    if args.auto and len(files_to_process) > 1:
        logger.info(f"Auto-switching to batch mode for {len(files_to_process)} files")
        use_batch = True
    
    if json_ready_files:
        logger.info(f"Found {len(json_ready_files)} files with JSON responses ready for markdown conversion")
        for filename in json_ready_files:
            file_path = os.path.join(input_dir, filename)
            file_stem = os.path.splitext(filename)[0]
            file_output_dir = os.path.join(output_dir, file_stem)
            json_path = os.path.join(file_output_dir, f"{file_stem}_response.json")
            
            if process_json_file(json_path, file_stem, file_output_dir):
                logger.info(f"Successfully converted JSON to markdown for {filename}")
            else:
                logger.error(f"Failed to convert JSON to markdown for {filename}")
    
    if use_batch and files_to_process:
        processed_count = process_batch_files(client, files_to_process, input_dir, output_dir, config)
        logger.info(f"Batch processing complete. Processed: {processed_count} files")
    elif files_to_process:
        processed_count = 0
        
        for filename in files_to_process:
            file_path = os.path.join(input_dir, filename)
            
            success = process_single_file(client, file_path, output_dir)
            if success:
                processed_count += 1
            
            import time
            time.sleep(1)
        
        logger.info(f"Processing complete. Processed: {processed_count} files")
    else:
        logger.info("No files need processing")

if __name__ == "__main__":
    main()