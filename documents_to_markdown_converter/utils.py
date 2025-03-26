#!/usr/bin/env python3
import os
import base64
import uuid
from pathlib import Path
from logging_setup import get_logger

logger = get_logger()

def is_already_transcribed(pdf_path, output_dir):
    pdf_stem = Path(pdf_path).stem
    pdf_output_dir = os.path.join(output_dir, pdf_stem)
    md_filename = f"{pdf_stem}.md"
    md_path = os.path.join(pdf_output_dir, md_filename)
    return os.path.exists(md_path)

def has_json_response(pdf_path, output_dir):
    pdf_stem = Path(pdf_path).stem
    pdf_output_dir = os.path.join(output_dir, pdf_stem)
    json_filename = f"{pdf_stem}_response.json"
    json_path = os.path.join(pdf_output_dir, json_filename)
    return os.path.exists(json_path)

def has_error(pdf_path, output_dir):
    pdf_stem = Path(pdf_path).stem
    pdf_output_dir = os.path.join(output_dir, pdf_stem)
    error_filename = f"{pdf_stem}_error"
    error_path = os.path.join(pdf_output_dir, error_filename)
    return os.path.exists(error_path)

def get_pdf_status(pdf_path, output_dir):
    """
    Returns the status of a PDF:
    - "transcribed": MD file exists
    - "json_ready": JSON response exists, but no MD file
    - "error": Error file exists
    - "needs_processing": Needs to be processed
    """
    if is_already_transcribed(pdf_path, output_dir):
        return "transcribed"
    elif has_error(pdf_path, output_dir):
        return "error"
    elif has_json_response(pdf_path, output_dir):
        return "json_ready"
    else:
        return "needs_processing"

def save_image_from_base64(base64_data, output_path):
    try:
        if not base64_data:
            return False
        
        if base64_data.startswith('data:'):
            base64_start = base64_data.find(';base64,')
            if base64_start != -1:
                base64_data = base64_data[base64_start + 8:]
            
        image_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as img_file:
            img_file.write(image_data)
        return True
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False

def generate_image_filename(page_index, img_id):
    return f"page{page_index}_{uuid.uuid4().hex[:8]}_{img_id}"

def ensure_directory_exists(directory_path):
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {e}")
        return False

class AttributeDict(dict):
    def __getattr__(self, key):
        return self[key]

def dict_to_attr_dict(d):
    if isinstance(d, dict):
        attr_dict = AttributeDict(d)
        for key, value in attr_dict.items():
            if isinstance(value, dict):
                attr_dict[key] = dict_to_attr_dict(value)
            elif isinstance(value, list):
                attr_dict[key] = [dict_to_attr_dict(item) if isinstance(item, dict) else item for item in value]
        return attr_dict
    return d