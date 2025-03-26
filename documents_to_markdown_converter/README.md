# Document to Markdown Converter

A tool for converting PDF documents (especially slides) to Markdown format using the Mistral API for OCR and content generation.

## Features

-   Convert PDF documents/slides to Markdown.
-   Uses Mistral API for potentially higher quality text extraction and formatting compared to basic OCR.
-   Extracts and saves images from PDF pages.
-   Support for batch processing of multiple PDFs.
-   Auto-switch to batch mode when multiple PDFs are detected in the input directory.
-   Skips already processed files (based on existing output).
-   Can re-process existing JSON responses (if available from previous runs) into Markdown.
-   Detailed logging for monitoring progress and debugging.

## Requirements

-   Python 3.6+
-   Dependencies listed in `requirements.txt` (`mistralai`, `tqdm`, `Pillow`, `python-dotenv`)
-   A Mistral API Key

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>/documents_to_markdown_converter
    ```
2.  **Install dependencies:**
    It's recommended to use a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```
3.  **Configure API Key:**
    -   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    -   Edit the `.env` file and add your Mistral API key:
        ```
        MISTRAL_API_KEY=your_api_key_here
        ```
    *Note: The `.env` file is ignored by Git (it will be added to `.gitignore` later) to prevent accidentally committing your key.*

4.  **Prepare Input:**
    Place the PDF files you want to convert into the `input` directory (or specify a different directory using the `--input` option).

## Usage

Run the main script from the `documents_to_markdown_converter` directory:

```bash
python main.py [options]
```

### Options

-   `--input`, `-i`: Input directory containing PDF files (default: `"input"`)
-   `--output`, `-o`: Output directory for markdown files and extracted images (default: `"output"`)
-   `--batch`, `-b`: Force batch processing mode for multiple PDFs.
-   `--auto`, `-a`: Automatically switch to batch processing if multiple PDFs are found in the input directory (this is often the default behavior if `--batch` isn't specified).
-   `--debug`, `-d`: Enable debug level logging for more detailed output.

### Examples

**Process all PDFs in the default `input` directory:**
```bash
python main.py
```

**Process PDFs from a specific input directory to a specific output directory:**
```bash
python main.py --input /path/to/my/pdfs --output /path/to/markdown/output
```

**Force batch mode (useful if auto-detection fails):**
```bash
python main.py --batch
```

**Enable debug logging:**
```bash
python main.py --debug
```

## Project Structure

-   `main.py`: Main script orchestrating the conversion process.
-   `cli.py`: Handles command-line argument parsing.
-   `config.py`: Loads configuration, including the API key from `.env`.
-   `logging_setup.py`: Configures application logging.
-   `pdf_handling.py`: Contains functions for processing PDFs, extracting images, and interacting with the Mistral API.
-   `md_creation.py`: Responsible for generating the final Markdown output from processed data.
-   `utils.py`: General utility functions used across the project.
-   `requirements.txt`: Lists Python dependencies.
-   `.env.example`: Example environment file for API key configuration.
-   `input/`: Default directory for input PDF files.
-   `output/`: Default directory for output Markdown files and images.