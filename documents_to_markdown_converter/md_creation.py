#!/usr/bin/env python3
import os
import json
from pathlib import Path
from utils import save_image_from_base64, generate_image_filename, ensure_directory_exists, dict_to_attr_dict
from logging_setup import get_logger

logger = get_logger()

def process_markdown_content(response_data, pdf_stem, pdf_output_dir):
    images_dir = os.path.join(pdf_output_dir, "images")
    ensure_directory_exists(images_dir)
    
    md_filename = f"{pdf_stem}.md"
    md_path = os.path.join(pdf_output_dir, md_filename)
    
    combined_md = []
    processed_images = {}
    
    for page in response_data.pages:
        page_index = page.index
        page_md = page.markdown
        
        if hasattr(page, 'images') and page.images:
            for img in page.images:
                img_id = img.id
                
                if not hasattr(img, 'image_base64') or img.image_base64 is None:
                    logger.warning(f"Skipping image {img_id} - no base64 data available")
                    continue
                
                img_filename = generate_image_filename(page_index, img_id)
                img_path = os.path.join(images_dir, img_filename)
                
                if save_image_from_base64(img.image_base64, img_path):
                    page_md = page_md.replace(f"![{img_id}]({img_id})", f"![{img_id}](images/{img_filename})")
                    processed_images[img_id] = f"images/{img_filename}"
                else:
                    logger.warning(f"Failed to save image {img_id}")
        
        combined_md.append(f"## Page {page_index}\n\n{page_md}\n\n")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {pdf_stem}\n\n")
        f.write("".join(combined_md))
    
    logger.info(f"Successfully saved {md_path} with {len(response_data.pages)} pages")
    return True

def process_json_file(json_path, pdf_stem, pdf_output_dir):
    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        if isinstance(json_data, dict):
            if "body" in json_data and isinstance(json_data["body"], dict) and "pages" in json_data["body"]:
                response_data = dict_to_attr_dict(json_data["body"])
            elif "pages" in json_data:
                response_data = dict_to_attr_dict(json_data)
            else:
                logger.warning(f"JSON file {json_path} has an unexpected structure. Attempting to process anyway.")
                response_data = dict_to_attr_dict(json_data)
                if not hasattr(response_data, "pages"):
                    logger.info(f"Creating synthetic page structure for {json_path}")
                    text = json.dumps(json_data, indent=2)
                    if isinstance(json_data, dict) and "text" in json_data:
                        text = json_data["text"]
                    
                    response_data = dict_to_attr_dict({
                        "pages": [
                            {
                                "index": 0,
                                "markdown": text,
                                "images": []
                            }
                        ]
                    })
        else:
            logger.warning(f"JSON file {json_path} contains non-dict data. Converting to string.")
            text = str(json_data)
            response_data = dict_to_attr_dict({
                "pages": [
                    {
                        "index": 0,
                        "markdown": text,
                        "images": []
                    }
                ]
            })
        
        success = process_markdown_content(response_data, pdf_stem, pdf_output_dir)
        if success:
            try:
                os.remove(json_path)
                logger.info(f"Deleted JSON file {json_path} after successful conversion")
            except Exception as e:
                logger.warning(f"Failed to delete JSON file {json_path}: {e}")
        return success
    except Exception as e:
        logger.error(f"Error processing JSON file {json_path}: {e}")
        error_path = os.path.join(pdf_output_dir, f"{pdf_stem}_error")
        with open(error_path, 'w') as f:
            f.write(f"Error: {str(e)}\n")
        return False

def save_plain_markdown(text_content, pdf_stem, pdf_output_dir):
    md_filename = f"{pdf_stem}.md"
    md_path = os.path.join(pdf_output_dir, md_filename)
    
    with open(md_path, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# {pdf_stem}\n\n")
        md_file.write(text_content)
    
    logger.info(f"Successfully saved {md_path}")
    return True
