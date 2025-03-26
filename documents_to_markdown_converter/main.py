#!/usr/bin/env python3
import os
import logging
from mistralai import Mistral
from config import load_config
from logging_setup import setup_logging, get_logger
from cli import parse_arguments, validate_directories
from pdf_handling import process_single_pdf, process_batch_pdfs
from utils import get_pdf_status
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
    
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.error(f"No PDF files found in {input_dir}")
        return
        
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    use_batch = args.batch
    pdfs_to_process = []
    json_ready_pdfs = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        status = get_pdf_status(pdf_path, output_dir)
        
        if status == "needs_processing":
            pdfs_to_process.append(pdf_file)
        elif status == "json_ready":
            json_ready_pdfs.append(pdf_file)
    
    if args.auto and len(pdfs_to_process) > 1:
        logger.info(f"Auto-switching to batch mode for {len(pdfs_to_process)} PDFs")
        use_batch = True
    
    if json_ready_pdfs:
        logger.info(f"Found {len(json_ready_pdfs)} PDFs with JSON responses ready for markdown conversion")
        for pdf_file in json_ready_pdfs:
            pdf_path = os.path.join(input_dir, pdf_file)
            pdf_stem = os.path.splitext(pdf_file)[0]
            pdf_output_dir = os.path.join(output_dir, pdf_stem)
            json_path = os.path.join(pdf_output_dir, f"{pdf_stem}_response.json")
            
            if process_json_file(json_path, pdf_stem, pdf_output_dir):
                logger.info(f"Successfully converted JSON to markdown for {pdf_file}")
            else:
                logger.error(f"Failed to convert JSON to markdown for {pdf_file}")
    
    if use_batch and pdfs_to_process:
        processed_count = process_batch_pdfs(client, pdfs_to_process, input_dir, output_dir, config)
        logger.info(f"Batch processing complete. Processed: {processed_count} PDFs")
    elif pdfs_to_process:
        processed_count = 0
        
        for pdf_file in pdfs_to_process:
            pdf_path = os.path.join(input_dir, pdf_file)
            
            success = process_single_pdf(client, pdf_path, output_dir)
            if success:
                processed_count += 1
            
            import time
            time.sleep(1)
        
        logger.info(f"Processing complete. Processed: {processed_count} PDFs")
    else:
        logger.info("No PDFs need processing")

if __name__ == "__main__":
    main()