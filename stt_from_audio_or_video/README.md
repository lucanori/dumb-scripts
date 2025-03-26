# Audio/Video Transcription Script

This script processes audio and video files, optimizes them if necessary using ffmpeg, and transcribes them using Groq's Whisper API.

## Features

- Automatically processes all audio/video files in the `to_transcribe` directory
- Checks if files need optimization (>40MB or unsupported format)
- Optimizes files using ffmpeg to ensure compatibility with Groq's API (converts to MP3 format under 40MB for Groq API compatibility)
- Transcribes audio/video using Groq's Whisper Large v3 model
- Saves transcriptions with a consistent naming convention
- Intelligently skips files that already have transcriptions (checks both original and processed file names)
- Avoids re-processing files if an optimized version already exists and meets size requirements
- Automatically deletes and recreates optimized files that don't meet size requirements

## Prerequisites

- Python 3.6+
- ffmpeg installed on your system
- Groq API key

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>/stt_from_audio_or_video
    ```
2.  **Install ffmpeg:**
    Make sure ffmpeg is installed on your system and accessible in your PATH.
    ```bash
    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg

    # Fedora/CentOS/RHEL
    sudo dnf install ffmpeg
    # Or potentially: sudo yum install ffmpeg (depending on repo setup)

    # macOS (using Homebrew)
    brew install ffmpeg

    # Windows
    # Download from https://ffmpeg.org/download.html and add to PATH
    ```
3.  **Install Python dependencies:**
    It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
4.  **Configure API Key:**
    -   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Edit the `.env` file and add your Groq API key:
        ```
        GROQ_API_KEY=your_api_key_here
        ```
    *Note: The `.env` file is ignored by Git (it will be added to `.gitignore` later).*

## Usage

1. Place your audio/video files in the `to_transcribe` directory.

2. Run the script:
   ```
   ./transcribe.py
   ```
   or
   ```
   python transcribe.py
   ```

3. The script will:
   - Check each file to see if it needs optimization
   - Optimize files if necessary and save them to `space_optimized_files`
   - Transcribe each file using Groq's API
   - Save transcriptions to the `transcriptions` directory

## Supported File Formats

The script supports the following file formats:
- flac
- mp3
- mp4
- mpeg
- mpga
- m4a
- ogg
- wav
- webm

Files with other formats or files larger than 40MB will be automatically processed with ffmpeg and converted to MP3 format. The script uses an adaptive bitrate approach, trying progressively lower bitrates until the file is under 40MB (Groq API's limit) while maintaining acceptable audio quality for transcription.

## Directory Structure

- `to_transcribe/`: Place your audio/video files here
- `transcriptions/`: Transcriptions will be saved here
- `space_optimized_files/`: Optimized versions of files will be saved here

## Troubleshooting

- If you encounter errors related to ffmpeg, make sure it's properly installed and available in your PATH.
- If you see API errors, verify that your Groq API key is correct in the `.env` file.
- The script includes a retry mechanism for API connection issues. If the Groq API is temporarily unavailable, the script will retry up to 3 times with increasing delays.
- If transcription fails after all retries, an error log file will be created in the `transcriptions` directory with details about the error.