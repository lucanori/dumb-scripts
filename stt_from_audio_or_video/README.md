# Audio/Video Transcription Script

This script processes audio and video files, optimizes them if necessary using ffmpeg, and transcribes them using configurable providers (Groq Whisper or Mistral Voxtral).

## Features

- Automatically processes all audio/video files in the `to_transcribe` directory
- Configurable transcription providers (Groq Whisper or Mistral Voxtral)
- Provider-specific optimization parameters and file size limits
- Optimizes files using ffmpeg to ensure compatibility with selected provider
- Saves transcriptions with a consistent naming convention
- Intelligently skips files that already have transcriptions (checks both original and processed file names)
- Avoids re-processing files if an optimized version already exists and meets size requirements
- Automatically deletes and recreates optimized files that don't meet size requirements
- Provider-specific error handling and retry logic

## Prerequisites

- Python 3.6+
- ffmpeg installed on your system
- API key for chosen provider (Groq and/or Mistral)

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
    -   Edit the `.env` file and configure your provider and API keys:
        ```bash
        # Choose your provider: "groq" or "mistral"
        TRANSCRIPTION_PROVIDER=groq
        
        # Add your API key(s)
        GROQ_API_KEY=your_groq_api_key_here
        MISTRAL_API_KEY=your_mistral_api_key_here
        ```
    *Note: The `.env` file is ignored by Git (it will be added to `.gitignore` later).*

## Usage

1. **Configure your provider** in `.env`:
   ```bash
   # For Groq Whisper
   TRANSCRIPTION_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   
   # For Mistral Voxtral
   TRANSCRIPTION_PROVIDER=mistral
   MISTRAL_API_KEY=your_mistral_api_key_here
   ```

2. Place your audio/video files in the `to_transcribe` directory.

3. Run the script:
   ```
   ./transcribe.py
   ```
   or
   ```
   python transcribe.py
   ```

4. The script will:
   - Display which provider is being used
   - Check each file to see if it needs optimization based on provider limits
   - Optimize files if necessary and save them to `space_optimized_files`
   - Transcribe each file using the configured provider
   - Save transcriptions to the `transcriptions` directory
   - Provide a summary of processed files, including optimization statistics

### Example Output

```
Starting audio/video transcription process using GROQ provider...
Found 3 files to process.

[1/3] Processing: podcast.mp3
  File doesn't need optimization: podcast.mp3 (12.4 MB, format: .mp3)
Transcribing: podcast.mp3
Transcription saved to: transcriptions/podcast_transcription.txt

[2/3] Processing: interview.wav
  File needs optimization: interview.wav (45.2 MB, format: .wav)
Optimizing: interview.wav (target: 20 MB)
  Attempting optimization with bitrate: 64k
  Successfully optimized to 18.7 MB with bitrate 64k
  Optimization complete: 45.2 MB → 18.7 MB (saved 26.5 MB, 58.6%)
Transcribing: interview_processed.mp3
Transcription saved to: transcriptions/interview_transcription.txt
```

## Supported File Formats

Supported file formats vary by provider:

**Groq Whisper Provider:**
- **Audio**: flac, mp3, mpga, m4a, ogg, wav
- **Video**: mp4, mpeg, webm
- **Total formats**: 9 supported formats

**Mistral Voxtral Provider:**
- **Audio**: mp3, mpga, m4a, wav
- **Video**: mp4, mpeg, webm
- **Total formats**: 7 supported formats (no flac/ogg support)

### Automatic Optimization

Files larger than the provider's limit (25MB) or with unsupported formats will be automatically processed with ffmpeg and converted to MP3 format. The script uses provider-specific bitrate ladders:

1. **Bitrate progression**: Provider-specific adaptive bitrate reduction
2. **Audio settings**: Mono channel, 16kHz sample rate
3. **Target size**: 20MB (5MB margin under the 25MB limit)
4. **Quality preservation**: Maintains acceptable audio quality for transcription while maximizing space efficiency

### Optimization Statistics

The script provides detailed optimization feedback:
- Original file size and format
- Optimized file size and bitrate used
- Space saved in MB and percentage
- Processing time for each optimization step

## Provider Configuration

### Groq Whisper Provider
- **Model**: whisper-large-v3 (configurable via `GROQ_MODEL`)
- **Max file size**: 25MB
- **Supported formats**: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
- **Preprocessing**: Converts to MP3 with provider-specific bitrate ladder when needed
- **Recommended settings**:
  - `GROQ_MODEL`: Model to use for transcription - *Default: whisper-large-v3*
  - `GROQ_LANGUAGE`: Language code (e.g., en, es, fr) - *Optional, auto-detect if not specified*
  - `GROQ_TEMPERATURE`: Temperature for transcription (0.0-1.0) - *Default: 0.0 for most accurate results*

### Mistral Voxtral Provider
- **Model**: voxtral-small-2507 (configurable via `MISTRAL_MODEL`)
- **Max file size**: 25MB
- **Supported formats**: mp3, mp4, mpeg, mpga, m4a, wav, webm (no flac/ogg support)
- **Preprocessing**: Converts to MP3 with provider-specific bitrate ladder when needed
- **Recommended settings**:
  - `MISTRAL_MODEL`: Model to use for transcription - *Default: voxtral-small-2507*
  - `MISTRAL_LANGUAGE`: Language code (e.g., en, es, fr) - *Optional, auto-detect if not specified*
  - `MISTRAL_TEMPERATURE`: Temperature for transcription (0.0-1.0) - *Default: 0.0 for most accurate results*

### Key Differences

| Feature | Groq Whisper | Mistral Voxtral |
|---------|--------------|-----------------|
| **Model** | whisper-large-v3 (configurable) | voxtral-small-2507 (configurable) |
| **Format Support** | Includes flac, ogg | More limited (no flac/ogg) |
| **API Style** | Python SDK | Direct REST API |
| **Error Handling** | HTML error detection | JSON error responses |
| **Response Format** | verbose_json | json |

### Provider Selection Guide

**Choose Groq Whisper if you:**
- Need support for flac or ogg formats
- Prefer a more established Whisper implementation
- Want verbose JSON responses with additional metadata

**Choose Mistral Voxtral if you:**
- Need configurable model selection with voxtral-small-2507
- Prefer REST API integration
- Have primarily mp3/mp4/wav files

## Directory Structure

- `to_transcribe/`: Place your audio/video files here
- `transcriptions/`: Transcriptions will be saved here
- `space_optimized_files/`: Optimized versions of files will be saved here

## Troubleshooting

### Common Issues

- **ffmpeg errors**: Make sure ffmpeg is properly installed and available in your PATH.
- **API key errors**: Verify that your API key is correct in the `.env` file and matches the selected provider.
- **File format errors**: Check that your file format is supported by the chosen provider (see Provider Configuration above).

### Provider-Specific Issues

**Groq Whisper:**
- **Cloudflare 520 errors**: Temporary API connectivity issues - the script will automatically retry up to 3 times
- **HTML error pages**: Indicates API overload or maintenance - retry later
- **Large file handling**: Files are automatically optimized using progressive bitrate reduction

**Mistral Voxtral:**
- **JSON error responses**: Check the error log file in `transcriptions/` for detailed error messages
- **Unsupported formats**: Convert flac/ogg files to mp3 before processing or switch to Groq
- **Model configuration**: Ensure `MISTRAL_MODEL` is set correctly if not using the default

### Error Recovery

- The script includes a retry mechanism for API connection issues. If the provider API is temporarily unavailable, the script will retry up to 3 times with increasing delays.
- If transcription fails after all retries, an error log file will be created in the `transcriptions` directory with details about the error, including the provider used.
- Optimization failures are logged with specific bitrate attempts and file sizes to help diagnose space issues.

### Performance Tips

- For best results, use `TEMPERATURE=0.0` for most accurate transcriptions
- Specify the `LANGUAGE` parameter if you know the source language to improve accuracy
- For large files, the script automatically optimizes them, but pre-converting to mono 16kHz MP3 can speed up processing