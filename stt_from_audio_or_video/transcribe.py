#!/usr/bin/env python3

import os
import sys
import subprocess
import pathlib
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from groq import Groq
import mimetypes
import requests
import json

load_dotenv()

TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if TRANSCRIPTION_PROVIDER == "groq":
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not found in .env file")
        sys.exit(1)
    groq_api_key = GROQ_API_KEY
    mistral_api_key = None
elif TRANSCRIPTION_PROVIDER == "mistral":
    if not MISTRAL_API_KEY:
        print("Error: MISTRAL_API_KEY not found in .env file")
        sys.exit(1)
    mistral_api_key = MISTRAL_API_KEY
    groq_api_key = None
else:
    print(f"Error: Unsupported provider '{TRANSCRIPTION_PROVIDER}'. Supported providers: groq, mistral")
    sys.exit(1)


class TranscriptionProvider(ABC):
    
    @abstractmethod
    def transcribe(self, file_path: str, file_name: str) -> str:
        pass
    
    @abstractmethod
    def get_max_file_size_mb(self) -> int:
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        pass
    
    @abstractmethod
    def get_optimization_settings(self) -> Dict[str, Any]:
        pass


class GroqProvider(TranscriptionProvider):
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.max_file_size_mb = 25
        self.supported_formats = ['.flac', '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.ogg', '.wav', '.webm']
        self.model = os.getenv("GROQ_MODEL", "whisper-large-v3")
        self.response_format = "verbose_json"
        self.language = os.getenv("GROQ_LANGUAGE", None)
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.0"))
        self.optimization_settings = {
            'target_extension': '.mp3',
            'sample_rate': '16000',
            'channels': 1,
            'bitrate_ladder': ['64k', '32k', '16k', '8k']
        }
    
    def transcribe(self, file_path: str, file_name: str) -> str:
        with open(file_path, "rb") as file:
            file_content = file.read()
            
            transcription_params = {
                "file": (file_name, file_content),
                "model": self.model,
                "response_format": self.response_format,
                "temperature": self.temperature
            }
            
            if self.language:
                transcription_params["language"] = self.language
            
            transcription = self.client.audio.transcriptions.create(**transcription_params)
            
            if isinstance(transcription.text, str) and transcription.text.strip().startswith('<!DOCTYPE html>'):
                raise Exception("Received HTML error page instead of transcription")
            
            return transcription.text
    
    def get_max_file_size_mb(self) -> int:
        return self.max_file_size_mb
    
    def get_supported_formats(self) -> list[str]:
        return self.supported_formats
    
    def get_optimization_settings(self) -> Dict[str, Any]:
        return self.optimization_settings


class MistralProvider(TranscriptionProvider):
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mistral.ai/v1"
        self.max_file_size_mb = 25
        self.supported_formats = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        self.model = os.getenv("MISTRAL_MODEL", "voxtral-small-2507")
        self.language = os.getenv("MISTRAL_LANGUAGE", None)
        self.temperature = float(os.getenv("MISTRAL_TEMPERATURE", "0.0"))
        self.optimization_settings = {
            'target_extension': '.mp3',
            'sample_rate': '16000',
            'channels': 1,
            'bitrate_ladder': ['96k', '64k', '48k', '32k']
        }
    
    def transcribe(self, file_path: str, file_name: str) -> str:
        with open(file_path, "rb") as file:
            file_ext = os.path.splitext(file_name)[1].lower()
            content_type = {
                '.mp3': 'audio/mpeg',
                '.mp4': 'video/mp4',
                '.mpeg': 'video/mpeg',
                '.mpga': 'audio/mpeg',
                '.m4a': 'audio/mp4',
                '.wav': 'audio/wav',
                '.webm': 'audio/webm'
            }.get(file_ext, 'audio/mpeg')
            
            files = {
                'file': (file_name, file, content_type)
            }
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            data = {
                'model': self.model,
                'response_format': 'json'
            }
            
            if self.language:
                data['language'] = self.language
            
            if self.temperature != 0.0:
                data['temperature'] = str(self.temperature)
            
            response = requests.post(
                f"{self.base_url}/audio/transcriptions",
                files=files,
                headers=headers,
                data=data,
                timeout=300
            )
            
            if response.status_code != 200:
                error_info = f"Mistral API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_info += f" - {error_detail.get('error', {}).get('message', response.text)}"
                except:
                    error_info += f" - {response.text}"
                raise Exception(error_info)
            
            result = response.json()
            
            if 'text' not in result:
                raise Exception("No transcription text in response")
            
            return result['text']
    
    def get_max_file_size_mb(self) -> int:
        return self.max_file_size_mb
    
    def get_supported_formats(self) -> list[str]:
        return self.supported_formats
    
    def get_optimization_settings(self) -> Dict[str, Any]:
        return self.optimization_settings


class ProviderFactory:
    
    @staticmethod
    def create_provider(provider_name: str, groq_key: Optional[str] = None, mistral_key: Optional[str] = None) -> TranscriptionProvider:
        if provider_name == "groq":
            if not groq_key:
                raise ValueError("Groq API key is required for Groq provider")
            return GroqProvider(groq_key)
        elif provider_name == "mistral":
            if not mistral_key:
                raise ValueError("Mistral API key is required for Mistral provider")
            return MistralProvider(mistral_key)
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")


provider = ProviderFactory.create_provider(TRANSCRIPTION_PROVIDER, groq_api_key, mistral_api_key)

SCRIPT_DIR = pathlib.Path(__file__).parent.absolute()
TO_TRANSCRIBE_DIR = SCRIPT_DIR / "to_transcribe"
TRANSCRIPTIONS_DIR = SCRIPT_DIR / "transcriptions"
OPTIMIZED_FILES_DIR = SCRIPT_DIR / "space_optimized_files"

TO_TRANSCRIBE_DIR.mkdir(exist_ok=True)
TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)
OPTIMIZED_FILES_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTENSIONS = provider.get_supported_formats()

def get_file_size_mb(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)

def get_transcription_path(file_path):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    return TRANSCRIPTIONS_DIR / f"{file_name}_transcription.txt"

def transcription_exists(file_path):
    original_transcription = get_transcription_path(file_path)
    if original_transcription.exists():
        return True
    
    optimized_file_path = get_optimized_file_path(file_path)
    optimized_file_name = os.path.basename(optimized_file_path)
    optimized_transcription = TRANSCRIPTIONS_DIR / f"{os.path.splitext(optimized_file_name)[0]}_transcription.txt"
    if optimized_transcription.exists():
        return True
    
    return False

def get_optimized_file_path(file_path):
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    settings = provider.get_optimization_settings()
    target_extension = settings['target_extension']
    return OPTIMIZED_FILES_DIR / f"{file_name}_processed{target_extension}"

def needs_optimization(file_path):
    file_size = get_file_size_mb(file_path)
    file_ext = os.path.splitext(file_path)[1].lower()
    max_size = provider.get_max_file_size_mb()
    
    return file_size > max_size or file_ext not in SUPPORTED_EXTENSIONS

def check_processed_file(file_path):
    processed_path = get_optimized_file_path(file_path)
    target_size_mb = provider.get_max_file_size_mb() - 5
    
    if not os.path.exists(processed_path):
        return None
    
    file_size = get_file_size_mb(processed_path)
    if file_size <= target_size_mb:
        return processed_path
    
    print(f"  Existing processed file is too large ({file_size:.2f} MB > {target_size_mb} MB), deleting and recreating")
    os.remove(processed_path)
    return None

def optimize_file(file_path):
    input_file = str(file_path)
    output_file = str(get_optimized_file_path(file_path))
    target_size_mb = provider.get_max_file_size_mb() - 5
    
    settings = provider.get_optimization_settings()
    sample_rate = settings['sample_rate']
    channels = settings['channels']
    bitrate_ladder = settings['bitrate_ladder']
    
    file_ext = os.path.splitext(file_path)[1].lower()
    
    print(f"Optimizing: {os.path.basename(file_path)} (target: {target_size_mb} MB)")
    
    for bitrate in bitrate_ladder:
        try:
            if file_ext in ['.mp3', '.mpga', '.m4a', '.ogg', '.wav', '.flac']:
                cmd = [
                    'ffmpeg', '-y', '-i', input_file, '-b:a', bitrate,
                    '-ac', str(channels), '-ar', sample_rate, output_file
                ]
            else:
                cmd = [
                    'ffmpeg', '-y', '-i', input_file, '-vn', '-b:a', bitrate,
                    '-ac', str(channels), '-ar', sample_rate, output_file
                ]
            
            print(f"  Attempting optimization with bitrate: {bitrate}")
            subprocess.run(cmd, check=True, capture_output=True)
            
            file_size = get_file_size_mb(output_file)
            if file_size <= target_size_mb:
                print(f"  Successfully optimized to {file_size:.2f} MB with bitrate {bitrate}")
                return output_file
            else:
                print(f"  File still too large: {file_size:.2f} MB > {target_size_mb} MB, trying lower bitrate")
        
        except subprocess.CalledProcessError as e:
            print(f"  Error optimizing file with bitrate {bitrate}: {e}")
            print(f"  ffmpeg stderr: {e.stderr.decode()}")
    
    print(f"  Failed to optimize file under {target_size_mb} MB after trying all bitrates")
    
    if os.path.exists(output_file):
        file_size = get_file_size_mb(output_file)
        print(f"  Using best effort result: {file_size:.2f} MB")
        return output_file
    
    return None

def transcribe_file(file_path, max_retries=3, retry_delay=5):
    file_name = os.path.basename(file_path)
    print(f"Transcribing: {file_name}")
    
    for attempt in range(max_retries):
        try:
            transcription_text = provider.transcribe(file_path, file_name)
            
            transcription_path = get_transcription_path(file_path)
            with open(transcription_path, "w", encoding="utf-8") as f:
                f.write(transcription_text)
            
            print(f"Transcription saved to: {transcription_path}")
            return True
            
        except Exception as e:
            if TRANSCRIPTION_PROVIDER == "groq":
                if "520" in str(e) or "Cloudflare" in str(e) or "HTML error page" in str(e):
                    error_msg = "Groq API connection error (Cloudflare 520)"
                else:
                    error_msg = str(e)
            else:
                error_msg = str(e)
                
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Error transcribing file: {error_msg}")
                print(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"Error transcribing file after {max_retries} attempts: {error_msg}")
                
                error_log_path = TRANSCRIPTIONS_DIR / f"{os.path.splitext(file_name)[0]}_error.log"
                with open(error_log_path, "w", encoding="utf-8") as f:
                    f.write(f"Error transcribing file: {error_msg}\n")
                    f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"File: {file_path}\n")
                    f.write(f"Provider: {TRANSCRIPTION_PROVIDER}\n")
                
                return False

def process_files():
    files = [f for f in TO_TRANSCRIBE_DIR.iterdir() if f.is_file()]
    
    if not files:
        print("No files found in the to_transcribe directory.")
        return
    
    print(f"Found {len(files)} files to process.")
    
    stats = {
        "total": len(files),
        "skipped": 0,
        "optimized": 0,
        "transcribed": 0,
        "failed": 0
    }
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{stats['total']}] Processing: {file_path.name}")
        
        if transcription_exists(file_path):
            print(f"  Transcription already exists for: {file_path.name}")
            stats["skipped"] += 1
            continue
        
        existing_processed = check_processed_file(file_path)
        if existing_processed:
            print(f"  Using existing processed file: {os.path.basename(existing_processed)} "
                  f"({get_file_size_mb(existing_processed):.2f} MB)")
            file_to_transcribe = existing_processed
        else:
            file_size_mb = get_file_size_mb(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if needs_optimization(file_path):
                print(f"  File needs optimization: {file_path.name} ({file_size_mb:.2f} MB, format: {file_ext})")
                optimized_path = optimize_file(file_path)
                if optimized_path:
                    file_to_transcribe = optimized_path
                    stats["optimized"] += 1
                    
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
        
        success = transcribe_file(file_to_transcribe)
        if success:
            stats["transcribed"] += 1
        else:
            stats["failed"] += 1
    
    print("\n" + "="*50)
    print("Transcription Process Summary:")
    print(f"  Total files processed: {stats['total']}")
    print(f"  Files skipped (already transcribed): {stats['skipped']}")
    print(f"  Files optimized: {stats['optimized']}")
    print(f"  Files successfully transcribed: {stats['transcribed']}")
    print(f"  Files failed: {stats['failed']}")
    print("="*50)

if __name__ == "__main__":
    print(f"Starting audio/video transcription process using {TRANSCRIPTION_PROVIDER.upper()} provider...")
    process_files()
    print("Transcription process completed.")