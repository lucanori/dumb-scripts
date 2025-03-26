#!/usr/bin/env python3
import os
import json
import base64
import time
from pathlib import Path
from tqdm import tqdm
from mistralai import Mistral
from utils import is_already_transcribed, has_json_response, has_error, get_pdf_status, dict_to_attr_dict, ensure_directory_exists
from md_creation import process_markdown_content, save_plain_markdown
from logging_setup import get_logger

logger = get_logger()

def process_single_pdf(client, pdf_path, output_dir):
    pdf_stem = Path(pdf_path).stem
    
    pdf_output_dir = os.path.join(output_dir, pdf_stem)
    ensure_directory_exists(pdf_output_dir)
    
    try:
        logger.info(f"Processing {pdf_path}...")
        
        uploaded_pdf = client.files.upload(
            file={
                "file_name": os.path.basename(pdf_path),
                "content": open(pdf_path, "rb"),
            },
            purpose="ocr"
        )
        
        signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
        
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url,
            },
            include_image_base64=True
        )
        
        return process_markdown_content(ocr_response, pdf_stem, pdf_output_dir)
        
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")
        return False

def create_batch_file(pdf_files, input_dir, batch_file):
    with open(batch_file, 'w') as file:
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_dir, pdf_file)
            
            with open(pdf_path, "rb") as pdf_content:
                base64_pdf = base64.b64encode(pdf_content.read()).decode('utf-8')
            
            entry = {
                "custom_id": pdf_file,
                "body": {
                    "document": {
                        "type": "document_url",
                        "document_url": f"data:application/pdf;base64,{base64_pdf}"
                    },
                    "include_image_base64": True
                }
            }
            file.write(json.dumps(entry) + '\n')

def process_batch_pdfs(client, pdf_files, input_dir, output_dir, config):
    logger.info("Setting up batch processing...")
    
    to_process = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        status = get_pdf_status(pdf_path, output_dir)
        if status == "needs_processing":
            to_process.append(pdf_file)
    
    if not to_process:
        logger.info("No PDFs to process. All are already transcribed, have JSON responses, or have errors.")
        return 0
    
    logger.info(f"Preparing to batch process {len(to_process)} PDFs...")
    
    batch_file = config["batch_file"]
    create_batch_file(to_process, input_dir, batch_file)
    
    logger.info("Uploading batch file...")
    batch_data = client.files.upload(
        file={
            "file_name": "ocr_batch.jsonl",
            "content": open(batch_file, "rb")
        },
        purpose="batch"
    )
    
    logger.info("Creating batch job...")
    created_job = client.batch.jobs.create(
        input_files=[batch_data.id],
        model="mistral-ocr-latest",
        endpoint="/v1/ocr",
        metadata={"job_type": "pdf_to_markdown"}
    )
    
    job_id = created_job.id
    logger.info(f"Batch job created with ID: {job_id}")
    logger.info("Monitoring batch job progress...")
    
    retrieved_job = client.batch.jobs.get(job_id=job_id)
    
    progress_bar = tqdm(total=retrieved_job.total_requests, desc="Processing PDFs")
    completed = 0
    
    while retrieved_job.status in ["QUEUED", "RUNNING"]:
        old_completed = completed
        completed = retrieved_job.succeeded_requests + retrieved_job.failed_requests
        
        progress_bar.update(completed - old_completed)
        
        logger.info(f"Status: {retrieved_job.status} | "
              f"Succeeded: {retrieved_job.succeeded_requests}/{retrieved_job.total_requests} | "
              f"Failed: {retrieved_job.failed_requests}")
        
        time.sleep(5)
        retrieved_job = client.batch.jobs.get(job_id=job_id)
    
    progress_bar.close()
    logger.info(f"Batch job completed with status: {retrieved_job.status}")
    
    logger.info("Downloading results...")
    output_path = config["results_file"]
    
    response = client.files.download(file_id=retrieved_job.output_file)
    
    response_content = b''
    for chunk in response.iter_bytes():
        response_content += chunk
    
    result_text = response_content.decode('utf-8')
    
    debug_path = config["debug_file"]
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(result_text)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result_text)
    
    processed_count = 0
    failed_count = 0
    
    logger.info("Processing batch results...")
    with open(output_path, 'r') as f:
        for line in f:
            try:
                result = json.loads(line)
                pdf_file = result["custom_id"]
                pdf_stem = Path(pdf_file).stem
                pdf_output_dir = os.path.join(output_dir, pdf_stem)
                
                ensure_directory_exists(pdf_output_dir)
                
                logger.info(f"Processing result for {pdf_file}...")
                
                if "response" in result:
                    logger.debug(f"Response keys: {list(result['response'].keys()) if isinstance(result['response'], dict) else 'Not a dict'}")
                    
                    if isinstance(result['response'], dict) and 'text' in result['response']:
                        if save_plain_markdown(result['response']['text'], pdf_stem, pdf_output_dir):
                            processed_count += 1
                        continue
                
                if result.get("error"):
                    logger.error(f"Error in batch result for {pdf_file}: {result['error']}")
                    failed_count += 1
                    continue
                
                if "response" in result and result["response"]:
                    response_data = result["response"]
                    
                    if isinstance(response_data, str):
                        try:
                            response_data = json.loads(response_data)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse response as JSON for {pdf_file}")
                            if save_plain_markdown(response_data, pdf_stem, pdf_output_dir):
                                processed_count += 1
                            continue
                    
                    if isinstance(response_data, dict):
                        logger.debug(f"Response data keys: {list(response_data.keys())}")
                        
                        if "text" in response_data:
                            if save_plain_markdown(response_data["text"], pdf_stem, pdf_output_dir):
                                processed_count += 1
                            continue
                        
                        elif "pages" in response_data:
                            ocr_response_obj = dict_to_attr_dict(response_data)
                            
                            if process_markdown_content(ocr_response_obj, pdf_stem, pdf_output_dir):
                                processed_count += 1
                                logger.info(f"Successfully processed {pdf_file}")
                            else:
                                logger.error(f"Failed to process response for {pdf_file}")
                                failed_count += 1
                        else:
                            json_path = os.path.join(pdf_output_dir, f"{pdf_stem}_response.json")
                            with open(json_path, 'w', encoding='utf-8') as json_file:
                                json.dump(response_data, json_file, indent=2)
                            
                            logger.warning(f"Saved raw response to {json_path} for investigation")
                            failed_count += 1
                else:
                    logger.error(f"No response data found for {pdf_file}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"Exception processing result: {e}")
                failed_count += 1
    
    try:
        os.remove(batch_file)
    except Exception as e:
        logger.warning(f"Could not remove batch file: {e}")
    
    return processed_count