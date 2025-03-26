#!/usr/bin/env python3
"""
Audio/Video Transcription Script

This script processes audio and video files from the 'to_transcribe' directory,
optimizes them if necessary using ffmpeg, and transcribes them using Groq's API.
"""

import os
import sys
import subprocess
import pathlib
import time
from dotenv import load_dotenv
from groq import Groq
import mimetypes
import requests
import json

# Load environment variables from .env file
load_dotenv()

# Get Groq API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY not found in .env file")
    sys.exit(1)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Define directories
SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
TO_TRANSCRIBE_DIR = SCRIPT_DIR / "to_transcribe"
TRANSCRIPTIONS_DIR = SCRIPT_DIR / "transcriptions"
OPTIMIZED_FILES_DIR = SCRIPT_DIR / "space_optimized_files"

# Ensure all directories exist
TO_TRANSCRIBE_DIR.mkdir(exist_ok=True)
TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)
OPTIMIZED_FILES_DIR.mkdir(exist_ok=True)

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.flac', '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.ogg', '.wav', '.webm']

def get_file_size_mb(file_path):
    """Get file size in megabytes"""
    return os.path.getsize(file_path) / (1024 * 1024)

def get_transcription_path(file_path):
    """Generate the path for the transcription file"""
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    return TRANSCRIPTIONS_DIR / f"{file_name}_transcription.txt"

def transcription_exists(file_path):
    """Check if a transcription exists for a file (either original or optimized)"""
    # Check for transcription of original file
    original_transcription = get_transcription_path(file_path)
    if original_transcription.exists():
        return True
    
    # Check for transcription of optimized file
    optimized_file_path = get_optimized_file_path(file_path)
    optimized_file_name = os.path.basename(optimized_file_path)
    optimized_transcription = TRANSCRIPTIONS_DIR / f"{os.path.splitext(optimized_file_name)[0]}_transcription.txt"
    if optimized_transcription.exists():
        return True
    
    return False

def get_optimized_file_path(file_path):
    """Generate the path for the optimized file"""
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    # Always use .mp3 extension for optimized files
    return OPTIMIZED_FILES_DIR / f"{file_name}_processed.mp3"

def needs_optimization(file_path):
    """Check if file needs optimization (>40MB or unsupported extension)"""
    file_size = get_file_size_mb(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    
    return file_size > 40 or file_ext not in SUPPORTED_EXTENSIONS

def check_processed_file(file_path, target_size_mb=35):
    """
    Check if a processed file already exists and meets size requirements.
    Returns:
    - None if no processed file exists or it doesn't meet requirements
    - Path to the processed file if it exists and meets requirements
    """
    processed_path = get_optimized_file_path(file_path)
    
    # Check if processed file exists
    if not os.path.exists(processed_path):
        return None
    
    # Check if processed file meets size requirements
    file_size = get_file_size_mb(processed_path)
    if file_size <= target_size_mb:
        return processed_path
    
    # If file exists but is too large, delete it
    print(f"  Existing processed file is too large ({file_size:.2f} MB > {target_size_mb} MB), deleting and recreating")
    os.remove(processed_path)
    return None

def optimize_file(file_path, target_size_mb=35):
    """
    Optimize file using ffmpeg to reduce size and ensure compatibility.
    Ensures the output file is under the target_size_mb (default 35MB).
    """
    input_file = str(file_path)
    output_file = str(get_optimized_file_path(file_path))
    
    # Get file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    
    # Try different bitrates until we get a file under the target size
    bitrates = ['64k', '32k', '24k', '16k', '8k']
    
    print(f"Optimizing: {os.path.basename(file_path)}")
    
    for bitrate in bitrates:
        try:
            # Always convert to MP3 for better space optimization and discrete audio quality
            if file_ext in ['.mp3', '.mpga', '.m4a', '.ogg', '.wav', '.flac']:
                # Audio file - convert to mp3 with reduced bitrate
                cmd = [
                    'ffmpeg', '-y', '-i', input_file, '-b:a', bitrate,
                    '-ac', '1', '-ar', '22050', output_file
                ]
            else:
                # Video file - extract audio and convert to mp3
                cmd = [
                    'ffmpeg', '-y', '-i', input_file, '-vn', '-b:a', bitrate,
                    '-ac', '1', '-ar', '22050', output_file
                ]
            
            print(f"  Attempting optimization with bitrate: {bitrate}")
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Check if the file is under the target size
            file_size = get_file_size_mb(output_file)
            if file_size <= target_size_mb:
                print(f"  Successfully optimized to {file_size:.2f} MB with bitrate {bitrate}")
                return output_file
            else:
                print(f"  File still too large: {file_size:.2f} MB > {target_size_mb} MB, trying lower bitrate")
        
        except subprocess.CalledProcessError as e:
            print(f"  Error optimizing file with bitrate {bitrate}: {e}")
            print(f"  ffmpeg stderr: {e.stderr.decode()}")
    
    # If we've tried all bitrates and still can't get under the target size
    print(f"  Failed to optimize file under {target_size_mb} MB after trying all bitrates")
    
    # Check if the last attempt produced a file
    if os.path.exists(output_file):
        file_size = get_file_size_mb(output_file)
        print(f"  Using best effort result: {file_size:.2f} MB")
        return output_file
    
    return None

def transcribe_file(file_path, max_retries=3, retry_delay=5):
    """Transcribe audio/video file using Groq API with retry mechanism"""
    file_name = os.path.basename(file_path)
    print(f"Transcribing: {file_name}")
    
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as file:
                file_content = file.read()
                
                # Try to transcribe using Groq API
                transcription = client.audio.transcriptions.create(
                    file=(file_name, file_content),
                    model="whisper-large-v3",
                    response_format="verbose_json",
                )
                
                # Check if the response contains HTML (error page)
                if isinstance(transcription.text, str) and transcription.text.strip().startswith('<!DOCTYPE html>'):
                    raise Exception("Received HTML error page instead of transcription")
                
                # Save transcription to file
                transcription_path = get_transcription_path(file_path)
                with open(transcription_path, "w", encoding="utf-8") as f:
                    f.write(transcription.text)
                
                print(f"Transcription saved to: {transcription_path}")
                return True
                
        except Exception as e:
            if "520" in str(e) or "Cloudflare" in str(e) or "HTML error page" in str(e):
                error_msg = "Groq API connection error (Cloudflare 520)"
            else:
                error_msg = str(e)
                
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Error transcribing file: {error_msg}")
                print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Error transcribing file after {max_retries} attempts: {error_msg}")
                
                # Save error information to a log file
                error_log_path = TRANSCRIPTIONS_DIR / f"{os.path.splitext(file_name)[0]}_error.log"
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Error transcribing file: {error_msg}\n")
                    f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"File: {file_path}\n")
                
                return False

def process_files():
    """Process all files in the to_transcribe directory"""
    # Get all files in the to_transcribe directory
    files = [f for f in TO_TRANSCRIBE_DIR.iterdir() if f.is_file()]
    
    if not files:
        print("No files found in the to_transcribe directory.")
        return
    
    print(f"Found {len(files)} files to process.")
    
    # Track statistics
    stats = {
        "total": len(files),
        "skipped": 0,
        "optimized": 0,
        "transcribed": 0,
        "failed": 0
    }
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{stats['total']}] Processing: {file_path.name}")
        
        # Check if transcription already exists (either for original or optimized file)
        if transcription_exists(file_path):
            print(f"  Transcription already exists for: {file_path.name}")
            stats["skipped"] += 1
            continue
        
        # Check if a processed file already exists and meets requirements
        existing_processed = check_processed_file(file_path)
        if existing_processed:
            print(f"  Using existing processed file: {os.path.basename(existing_processed)} "
                  f"({get_file_size_mb(existing_processed):.2f} MB)")
            file_to_transcribe = existing_processed
        else:
            # Check if file needs optimization
            file_size_mb = get_file_size_mb(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if needs_optimization(file_path):
                print(f"  File needs optimization: {file_path.name} ({file_size_mb:.2f} MB, format: {file_ext})")
                optimized_path = optimize_file(file_path)
                if optimized_path:
                    file_to_transcribe = optimized_path
                    stats["optimized"] += 1
                    
                    # Get optimized file size for comparison
                    optimized_size_mb = get_file_size_mb(optimized_path)
                    size_reduction = file_size_mb - optimized_size_mb
                    reduction_percent = (size_reduction / file_size_mb) * 100 if file_size_mb > 0 else 0
                    
                    print(f"  Optimization complete: {file_size_mb:.2f} MB → {optimized_size_mb:.2f} MB "
                          f"(saved {size_reduction:.2f} MB, {reduction_percent:.1f}%)")
                else:
                    print(f"  Skipping file due to optimization failure: {file_path.name}")
                    stats["failed"] += 1
                    continue
            else:
                print(f"  File doesn't need optimization: {file_path.name} ({file_size_mb:.2f} MB, format: {file_ext})")
                file_to_transcribe = file_path
        
        # Transcribe the file
        success = transcribe_file(file_to_transcribe)
        if success:
            stats["transcribed"] += 1
        else:
            stats["failed"] += 1
    
    # Print summary
    print("\n" + "="*50)
    print("Transcription Process Summary:")
    print(f"  Total files processed: {stats['total']}")
    print(f"  Files skipped (already transcribed): {stats['skipped']}")
    print(f"  Files optimized: {stats['optimized']}")
    print(f"  Files successfully transcribed: {stats['transcribed']}")
    print(f"  Files failed: {stats['failed']}")
    print("="*50)

if __name__ == "__main__":
    print("Starting audio/video transcription process...")
    process_files()
    print("Transcription process completed.")