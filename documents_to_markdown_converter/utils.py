#!/usr/bin/env python3
import os
import base64
import uuid
from pathlib import Path
from logging_setup import get_logger

logger = get_logger()

SUPPORTED_DOCUMENT_EXTENSIONS = {'.pdf', '.pptx', '.docx'}
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.avif'}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_DOCUMENT_EXTENSIONS | SUPPORTED_IMAGE_EXTENSIONS

def get_supported_files(directory):
    supported_files = []
    if not os.path.exists(directory):
        return supported_files
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            extension = Path(filename).suffix.lower()
            if extension in ALL_SUPPORTED_EXTENSIONS:
                supported_files.append(filename)
    
    return supported_files

def get_file_type(file_path):
    extension = Path(file_path).suffix.lower()
    if extension in SUPPORTED_DOCUMENT_EXTENSIONS:
        return "document"
    elif extension in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    else:
        return "unsupported"

def get_mime_type(file_path):
    extension = Path(file_path).suffix.lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.avif': 'image/avif'
    }
    return mime_types.get(extension, 'application/octet-stream')

def is_already_transcribed(file_path, output_dir):
    file_stem = Path(file_path).stem
    file_output_dir = os.path.join(output_dir, file_stem)
    md_filename = f"{file_stem}.md"
    md_path = os.path.join(file_output_dir, md_filename)
    return os.path.exists(md_path)

def has_json_response(file_path, output_dir):
    file_stem = Path(file_path).stem
    file_output_dir = os.path.join(output_dir, file_stem)
    json_filename = f"{file_stem}_response.json"
    json_path = os.path.join(file_output_dir, json_filename)
    return os.path.exists(json_path)

def has_error(file_path, output_dir):
    file_stem = Path(file_path).stem
    file_output_dir = os.path.join(output_dir, file_stem)
    error_filename = f"{file_stem}_error"
    error_path = os.path.join(file_output_dir, error_filename)
    return os.path.exists(error_path)

def get_file_status(file_path, output_dir):
    if is_already_transcribed(file_path, output_dir):
        return "transcribed"
    elif has_error(file_path, output_dir):
        return "error"
    elif has_json_response(file_path, output_dir):
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