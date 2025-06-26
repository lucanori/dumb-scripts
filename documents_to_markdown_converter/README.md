# Document to Markdown Converter

A tool for converting various document formats to Markdown using the Mistral API for OCR and content generation.

## Features

-   Convert multiple document formats to Markdown:
    -   **Documents**: PDF, PPTX (PowerPoint), DOCX (Word)
    -   **Images**: PNG, JPEG, AVIF
-   Uses Mistral API for high-quality text extraction and formatting with superior accuracy
-   Extracts and saves images from document pages
-   Support for batch processing of multiple files ⚠️ **Currently not working reliably**
-   Auto-switch to batch mode when multiple files are detected in the input directory
-   Single file processing is fast and reliable (recommended method)
-   Skips already processed files (based on existing output)
-   Can re-process existing JSON responses (if available from previous runs) into Markdown
-   Detailed logging for monitoring progress and debugging

## Supported File Types

The converter supports all file types available in Mistral OCR:

### Document Formats
- **PDF** (.pdf) - Portable Document Format files
- **PPTX** (.pptx) - Microsoft PowerPoint presentations
- **DOCX** (.docx) - Microsoft Word documents

### Image Formats
- **PNG** (.png) - Portable Network Graphics
- **JPEG** (.jpg, .jpeg) - Joint Photographic Experts Group
- **AVIF** (.avif) - AV1 Image File Format

All formats support complex layouts including tables, equations, multilingual text, and embedded images.

## Requirements

-   Python 3.8+
-   Dependencies listed in `requirements.txt` (`mistralai`, `tqdm`, `Pillow`, `python-dotenv`)
-   A Mistral API Key
-   uv (for fast dependency management)

## Setup

1.  **Install uv (if not already installed):**
    ```bash
    # Install uv using pip
    pip install uv
    
    # Or install system-wide without Python from GitHub releases:
    # curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>/documents_to_markdown_converter
    ```

3.  **Create virtual environment and install dependencies:**
    Using uv (recommended for faster installation):
    ```bash
    # Create virtual environment
    uv venv
    
    # Activate virtual environment
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    
    # Install dependencies with uv
    uv pip install -r requirements.txt
    ```
    
    Alternative with traditional pip (if uv is not available):
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
    -   Edit the `.env` file and add your Mistral API key:
        ```
        MISTRAL_API_KEY=your_api_key_here
        ```

5.  **Prepare Input:**
    Place the document files you want to convert into the `input` directory (or specify a different directory using the `--input` option).

## Usage

Run the main script from the `documents_to_markdown_converter` directory:

```bash
python main.py [options]
```

### Options

-   `--input`, `-i`: Input directory containing document files (default: `"input"`)
-   `--output`, `-o`: Output directory for markdown files and extracted images (default: `"output"`)
-   `--batch`, `-b`: Force batch processing mode for multiple files.
-   `--auto`, `-a`: Automatically switch to batch processing if multiple files are found in the input directory (this is often the default behavior if `--batch` isn't specified).
-   `--debug`, `-d`: Enable debug level logging for more detailed output.

### Examples

**Process all supported files in the default `input` directory:**
```bash
python main.py
```

**Process files from a specific input directory to a specific output directory:**
```bash
python main.py --input /path/to/my/documents --output /path/to/markdown/output
```

**Force batch mode (⚠️ currently not working reliably - see Known Issues below):**
```bash
python main.py --batch
```

**Enable debug logging:**
```bash
python main.py --debug
```

### Supported File Examples

The tool can process various file types:
- **PDFs**: Research papers, reports, scanned documents
- **PowerPoint**: Presentation slides with text and images  
- **Word Documents**: Articles, reports, documentation
- **Images**: Screenshots, photos of documents, diagrams

## Known Issues

### ⚠️ Batch Processing Currently Not Working Reliably

**Status**: Batch processing through the Mistral OCR API is experiencing significant issues as of now.

**Problems**:
- Batch requests consistently fail with "Internal error" responses
- API limitations with large file sizes in batch mode  
- Batch API validation errors when using file references
- Request size limits when embedding base64 data in batch requests

**Workaround**: 
- **Use single file processing** - this works reliably and is actually quite fast
- The tool will automatically process multiple files sequentially when batch mode fails
- Single file processing typically completes ~3-4 files per minute

**Investigation Status**:
- Root cause identified as Mistral OCR batch API limitations
- Batch API only accepts `document_url`/`image_url` (not file uploads)
- Large files (32MB+ when base64 encoded) exceed batch request limits

**Recommendation**: 
Until batch processing is fixed, stick with single file processing by avoiding the `--batch` flag. The tool will process each file individually, which is currently the most reliable method.

## Performance Benefits

The updated converter leverages Mistral OCR's superior capabilities:
- **High Accuracy**: 94.89% overall accuracy, 98.96% for scanned documents
- **Complex Layout Handling**: Preserves tables, equations, and document structure
- **Multilingual Support**: Handles diverse scripts and languages
- **Structured Output**: Generates clean Markdown instead of raw text

By using uv for dependency management, you'll also experience:
-   **10-100x faster** dependency installation and resolution
-   **Improved caching** that reduces redundant downloads
-   **Better dependency conflict resolution**

## Development

### Adding Dependencies
When adding new dependencies to the project:
```bash
# Add a new package
uv pip install package-name

# Update requirements.txt
uv pip freeze > requirements.txt
```

### Using uv for Tool Execution
You can also run the tool directly with uv without activating the virtual environment:
```bash
# Run with uv (automatically uses the project's virtual environment)
uv run python main.py [options]
```

## Project Structure

-   `main.py`: Main script orchestrating the conversion process.
-   `cli.py`: Handles command-line argument parsing.
-   `config.py`: Loads configuration, including the API key from `.env`.
-   `logging_setup.py`: Configures application logging.
-   `document_processing.py`: Contains functions for processing all document types, extracting images, and interacting with the Mistral API.
-   `md_creation.py`: Responsible for generating the final Markdown output from processed data.
-   `utils.py`: General utility functions including file type detection and support.
-   `requirements.txt`: Lists Python dependencies.
-   `.env.example`: Example environment file for API key configuration.
-   `input/`: Default directory for input document files.
-   `output/`: Default directory for output Markdown files and images.

For more information about uv, visit the [official documentation](https://docs.astral.sh/uv/).