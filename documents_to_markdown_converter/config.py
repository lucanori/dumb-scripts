#!/usr/bin/env python3
import os
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    env_path = Path(os.path.dirname(os.path.abspath(__file__))) / '.env'
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
    
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in .env file or environment variables")
    
    return {
        "api_key": api_key,
        "ocr_model": "mistral-ocr-latest",
        "batch_file": os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_batch.jsonl"),
        "results_file": os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_results.jsonl"),
        "debug_file": os.path.join(os.path.dirname(os.path.abspath(__file__)), "ocr_results_debug.jsonl")
    }