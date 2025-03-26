# Selfh.st Icon Downloader

This set of scripts downloads all PNG icons (including available `-light` variants) listed on the [selfh.st/icons](https://selfh.st/icons) page. It uses Puppeteer (via Node.js) to fetch the dynamically loaded page content and a shell script to parse the HTML and download the icons.

## Features

-   Fetches the latest icon list from `selfh.st/icons`.
-   Uses a local HTML cache (`icons_page.html`) to avoid refetching the page too often (configurable cache duration).
-   Downloads both standard and `-light` PNG icons if available.
-   Skips downloading icons that already exist in the target directory.
-   Provides progress updates during download (in non-debug mode).
-   Optional debug logging.

## Requirements

-   **Bash:** For running the main script.
-   **Node.js & npm:** For running the Puppeteer script (`fetch_icons_page.js`) to get the HTML source.
-   **ripgrep (`rg`):** A fast regex search tool used for extracting icon URLs from the HTML. Install via your package manager (e.g., `sudo apt install ripgrep`, `sudo pacman -S ripgrep`, `brew install ripgrep`).
-   **curl:** A command-line tool for transferring data, used for downloading the icons. Usually pre-installed on Linux/macOS.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-directory>/download_selfhst_icons
    ```
2.  **Install Node.js dependencies:**
    Navigate to the `download_selfhst_icons` directory and run:
    ```bash
    npm install
    ```
    This will install `puppeteer` and create a `node_modules` directory.

## Usage

Run the main shell script from the `download_selfhst_icons` directory:

```bash
./download_selfhst_icons.sh [options]
```

**Options:**

-   `--debug`: Enable detailed logging output during execution.

**Execution:**

The script will:
1.  Check if a cached `icons_page.html` exists and is recent enough (default: 7 days).
2.  If no valid cache exists, it runs `node fetch_icons_page.js` to get a fresh copy of the HTML.
3.  It parses `icons_page.html` using `rg` to find all PNG icon URLs.
4.  It iterates through the URLs, downloading each icon and its corresponding `-light` version (if it exists and isn't already present) into the `icons/` subdirectory.

Downloaded icons will be placed in the `icons/` directory within the script's folder.

## Notes

-   The `icons/` directory can become large and contains many files. It's recommended to add `icons/` to your `.gitignore` if you don't intend to commit the downloaded icons.
-   Similarly, `node_modules/` and `icons_page.html` should typically be added to `.gitignore`.
-   The first run might take a while as it needs to download all icons. Subsequent runs will be much faster as they only download missing icons or refresh the HTML cache if needed.