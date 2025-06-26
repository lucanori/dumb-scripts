#!/usr/bin/env python3
import os
import json
import base64
import time
from pathlib import Path
from tqdm import tqdm
from mistralai import Mistral
from utils import is_already_transcribed, has_json_response, has_error, get_file_status, dict_to_attr_dict, ensure_directory_exists, get_file_type, get_mime_type
from md_creation import process_markdown_content, save_plain_markdown
from logging_setup import get_logger

logger = get_logger()

def process_single_file(client, file_path, output_dir):
    file_stem = Path(file_path).stem
    
    file_output_dir = os.path.join(output_dir, file_stem)
    ensure_directory_exists(file_output_dir)
    
    try:
        logger.info(f"Processing {file_path}...")
        
        file_type = get_file_type(file_path)
        mime_type = get_mime_type(file_path)
        
        uploaded_file = client.files.upload(
            file={
                "file_name": os.path.basename(file_path),
                "content": open(file_path, "rb"),
            },
            purpose="ocr"
        )
        
        signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
        
        if file_type == "document":
            document_input = {
                "type": "document_url",
                "document_url": signed_url.url,
            }
        elif file_type == "image":
            document_input = {
                "type": "image_url", 
                "image_url": signed_url.url,
            }
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document=document_input,
            include_image_base64=True
        )
        
        return process_markdown_content(ocr_response, file_stem, file_output_dir)
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False

def create_batch_file(files, input_dir, batch_file, client):
    logger.info(f"Creating batch file for {len(files)} files...")
    uploaded_files = {}
    
    with open(batch_file, 'w') as file:
        for filename in files:
            file_path = os.path.join(input_dir, filename)
            file_type = get_file_type(file_path)
            mime_type = get_mime_type(file_path)
            
            logger.debug(f"Processing {filename}: type={file_type}, mime={mime_type}")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.warning(f"Skipping empty file: {filename}")
                continue
            
            if file_size > 50 * 1024 * 1024:  # 50MB
                logger.warning(f"File {filename} is large ({file_size/1024/1024:.1f}MB) - may cause batch processing issues")
            
            try:
                logger.debug(f"Uploading {filename} to get file_id...")
                uploaded_file = client.files.upload(
                    file={
                        "file_name": filename,
                        "content": open(file_path, "rb"),
                    },
                    purpose="ocr"
                )
                uploaded_files[filename] = uploaded_file.id
                logger.debug(f"Uploaded {filename} with file_id: {uploaded_file.id}")
            except Exception as e:
                logger.error(f"Failed to upload {filename}: {e}")
                continue
            
            if file_type == "document":
                document_input = {
                    "type": "file_id",
                    "file_id": uploaded_file.id
                }
            elif file_type == "image":
                document_input = {
                    "type": "file_id", 
                    "file_id": uploaded_file.id
                }
            else:
                logger.warning(f"Skipping unsupported file type: {filename}")
                continue
            
            entry = {
                "custom_id": filename,
                "body": {
                    "model": "mistral-ocr-latest",
                    "document": document_input,
                    "include_image_base64": True
                }
            }
            file.write(json.dumps(entry) + '\n')
            logger.debug(f"Added {filename} to batch file using file_id")
    
    with open(batch_file, 'r') as f:
        first_line = f.readline()
        logger.debug(f"First batch entry: {first_line[:300]}...")
    
    return uploaded_files

def process_batch_files(client, files, input_dir, output_dir, config):
    logger.info("Setting up batch processing...")
    
    to_process = []
    for filename in files:
        file_path = os.path.join(input_dir, filename)
        status = get_file_status(file_path, output_dir)
        if status == "needs_processing":
            to_process.append(filename)
    
    if not to_process:
        logger.info("No files to process. All are already transcribed, have JSON responses, or have errors.")
        return 0
    
    logger.info(f"Preparing to batch process {len(to_process)} files...")
    
    batch_file = config["batch_file"]
    uploaded_files = create_batch_file(to_process, input_dir, batch_file, client)
    
    if not uploaded_files:
        logger.error("No files were successfully uploaded for batch processing")
        return 0
    
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
        metadata={"job_type": "documents_to_markdown"}
    )
    
    job_id = created_job.id
    logger.info(f"Batch job created with ID: {job_id}")
    logger.info("Monitoring batch job progress...")
    
    retrieved_job = client.batch.jobs.get(job_id=job_id)
    
    progress_bar = tqdm(total=retrieved_job.total_requests, desc="Processing files")
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
    
    logger.debug(f"Job details: succeeded={retrieved_job.succeeded_requests}, "
                f"failed={retrieved_job.failed_requests}, "
                f"total={retrieved_job.total_requests}")
    
    if hasattr(retrieved_job, 'error_file') and retrieved_job.error_file:
        logger.info("Found error file, downloading error details...")
        try:
            error_response = client.files.download(file_id=retrieved_job.error_file)
            error_content = b''
            for chunk in error_response.iter_bytes():
                error_content += chunk
            error_text = error_content.decode('utf-8')
            logger.error(f"Batch job errors:\n{error_text}")
        except Exception as e:
            logger.error(f"Could not download error file: {e}")
    
    if not retrieved_job.output_file:
        logger.error("Batch job completed but no output file is available")
        if retrieved_job.failed_requests > 0:
            logger.error(f"Batch job had {retrieved_job.failed_requests} failed requests")
        
        if hasattr(retrieved_job, 'errors') and retrieved_job.errors:
            logger.error(f"Job-level errors: {retrieved_job.errors}")
        
        logger.info("Cleaning up uploaded files...")
        for filename, file_id in uploaded_files.items():
            try:
                client.files.delete(file_id=file_id)
                logger.debug(f"Deleted uploaded file {filename} (ID: {file_id})")
            except Exception as e:
                logger.warning(f"Could not delete uploaded file {filename}: {e}")
        
        return 0
    
    logger.info("Downloading results...")
    output_path = config["results_file"]
    
    try:
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
    except Exception as e:
        logger.error(f"Error downloading batch results: {e}")
        return 0
    
    processed_count = 0
    failed_count = 0
    
    logger.info("Processing batch results...")
    with open(output_path, 'r') as f:
        for line in f:
            try:
                result = json.loads(line)
                filename = result["custom_id"]
                file_stem = Path(filename).stem
                file_output_dir = os.path.join(output_dir, file_stem)
                
                ensure_directory_exists(file_output_dir)
                
                logger.info(f"Processing result for {filename}...")
                
                if "response" in result:
                    logger.debug(f"Response keys: {list(result['response'].keys()) if isinstance(result['response'], dict) else 'Not a dict'}")
                    
                    if isinstance(result['response'], dict) and 'text' in result['response']:
                        if save_plain_markdown(result['response']['text'], file_stem, file_output_dir):
                            processed_count += 1
                        continue
                
                if result.get("error"):
                    logger.error(f"Error in batch result for {filename}: {result['error']}")
                    failed_count += 1
                    continue
                
                if "response" in result and result["response"]:
                    response_data = result["response"]
                    
                    if isinstance(response_data, str):
                        try:
                            response_data = json.loads(response_data)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse response as JSON for {filename}")
                            if save_plain_markdown(response_data, file_stem, file_output_dir):
                                processed_count += 1
                            continue
                    
                    if isinstance(response_data, dict):
                        logger.debug(f"Response data keys: {list(response_data.keys())}")
                        
                        if "text" in response_data:
                            if save_plain_markdown(response_data["text"], file_stem, file_output_dir):
                                processed_count += 1
                            continue
                        
                        elif "pages" in response_data:
                            ocr_response_obj = dict_to_attr_dict(response_data)
                            
                            if process_markdown_content(ocr_response_obj, file_stem, file_output_dir):
                                processed_count += 1
                                logger.info(f"Successfully processed {filename}")
                            else:
                                logger.error(f"Failed to process response for {filename}")
                                failed_count += 1
                        else:
                            json_path = os.path.join(file_output_dir, f"{file_stem}_response.json")
                            with open(json_path, 'w', encoding='utf-8') as json_file:
                                json.dump(response_data, json_file, indent=2)
                            
                            logger.warning(f"Saved raw response to {json_path} for investigation")
                            failed_count += 1
                else:
                    logger.error(f"No response data found for {filename}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"Exception processing result: {e}")
                failed_count += 1
    
    logger.info("Cleaning up uploaded files...")
    for filename, file_id in uploaded_files.items():
        try:
            client.files.delete(file_id=file_id)
            logger.debug(f"Deleted uploaded file {filename} (ID: {file_id})")
        except Exception as e:
            logger.warning(f"Could not delete uploaded file {filename}: {e}")
    
    try:
        os.remove(batch_file)
    except Exception as e:
        logger.warning(f"Could not remove batch file: {e}")
    
    return processed_count