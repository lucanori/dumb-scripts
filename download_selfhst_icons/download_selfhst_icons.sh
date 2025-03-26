#!/bin/bash

# --- Configuration ---
BASEDIR=$(dirname "$0")
DOWNLOAD_DIR="$BASEDIR/icons"
HTML_FILE="$BASEDIR/icons_page.html"
CACHE_DAYS=7 # How many days before refreshing the HTML cache
DEBUG=false

# --- Argument Parsing ---
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --debug) DEBUG=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# --- Helper Functions ---
log_debug() {
    if [ "$DEBUG" = true ]; then
        echo "[DEBUG] $1"
    fi
}

log_info() {
     if [ "$DEBUG" = true ]; then
        echo "[INFO] $1"
     fi
}

log_error() {
    # Always print errors
    echo "[ERROR] $1" >&2
}

update_status() {
    if [ "$DEBUG" = false ]; then
        # Use \r to return to the beginning of the line and overwrite
        printf "\rDownloaded: %d | Existed: %d | Light Dl: %d | Light Ex: %d | Total: %d" \
               "$DOWNLOADED_COUNT" "$EXISTED_COUNT" "$LIGHT_DOWNLOADED_COUNT" "$LIGHT_EXISTED_COUNT" "$TOTAL_ICONS"
    fi
}


fetch_html() {
    log_info "Fetching fresh icons page..."
    node "$BASEDIR/fetch_icons_page.js"
    if [ $? -ne 0 ]; then
        log_error "Failed to fetch HTML page via Node.js script."
        return 1
    fi
    log_debug "Moving fetched HTML file from ./icons_page.html to $HTML_FILE..."
    mv ./icons_page.html "$HTML_FILE"
    if [ $? -ne 0 ]; then
        log_error "Failed to move HTML file to $HTML_FILE."
        return 1
    fi
    log_info "Successfully fetched and saved $HTML_FILE."
    return 0
}

# --- Main Script ---
mkdir -p "$DOWNLOAD_DIR"
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
DOWNLOADED_COUNT=0
EXISTED_COUNT=0
LIGHT_DOWNLOADED_COUNT=0
LIGHT_EXISTED_COUNT=0
PROCESSED_COUNT=0 # To track progress for the live counter

log_info "Script started at $START_TIME"

# --- HTML Cache Handling ---
REFETCH_HTML=false
if [ ! -f "$HTML_FILE" ]; then
    log_info "HTML file $HTML_FILE not found."
    REFETCH_HTML=true
else
    log_debug "Checking age of $HTML_FILE..."
    if find "$HTML_FILE" -mtime +"$((CACHE_DAYS - 1))" -print -quit | grep -q .; then
        log_info "$HTML_FILE is older than $CACHE_DAYS days."
        rm "$HTML_FILE"
        log_debug "Removed old $HTML_FILE."
        REFETCH_HTML=true
    else
        log_info "Using cached HTML file: $HTML_FILE (less than $CACHE_DAYS days old)."
    fi
fi

if [ "$REFETCH_HTML" = true ]; then
    fetch_html || exit 1 # Exit if fetching fails
fi

# --- Icon URL Extraction ---
log_info "Extracting PNG icon URLs from $HTML_FILE..."
ICON_URLS=$(rg -o 'href="([^"]+/png/[^"]+\.png)"[^>]*>PNG</a>' "$HTML_FILE" --replace '$1')

if [ -z "$ICON_URLS" ]; then
    log_error "No PNG icon URLs found in $HTML_FILE. Check the HTML structure or the regex."
    exit 1
fi

TOTAL_ICONS=$(echo "$ICON_URLS" | wc -l)
log_info "Found $TOTAL_ICONS potential PNG icons."
# Initial status print for non-debug mode
if [ "$DEBUG" = false ]; then
    echo "Processing icons..."
    update_status # Show initial zero counts
fi

# --- Download Loop ---
while IFS= read -r URL; do
    if [ -z "$URL" ]; then
        continue
    fi

    FILENAME=$(basename "$URL")
    FILEPATH="$DOWNLOAD_DIR/$FILENAME"

    # Download main icon
    if [ ! -f "$FILEPATH" ]; then
        log_debug "Downloading $FILENAME..."
        curl -s -L -o "$FILEPATH" "$URL"
        if [ $? -ne 0 ]; then
            log_error "Failed to download $FILENAME from $URL"
        else
            ((DOWNLOADED_COUNT++))
            log_debug "Successfully downloaded $FILENAME."
        fi
    else
        log_debug "$FILENAME already exists, skipping..."
        ((EXISTED_COUNT++))
    fi

    # Check and download light version
    LIGHT_FILENAME="${FILENAME%.*}-light.${FILENAME##*.}"
    LIGHT_URL="${URL%/*}/$LIGHT_FILENAME"
    LIGHT_FILEPATH="$DOWNLOAD_DIR/$LIGHT_FILENAME"

    if [ ! -f "$LIGHT_FILEPATH" ]; then
        log_debug "Checking for light version of $FILENAME..."
        if curl -s -L --head --fail "$LIGHT_URL" > /dev/null; then
            log_debug "Downloading light version $LIGHT_FILENAME..."
            curl -s -L -o "$LIGHT_FILEPATH" "$LIGHT_URL"
            if [ $? -ne 0 ]; then
                log_error "Failed to download light version $LIGHT_FILENAME from $LIGHT_URL"
            else
                 ((LIGHT_DOWNLOADED_COUNT++))
                 log_debug "Successfully downloaded light version $LIGHT_FILENAME."
            fi
        else
            log_debug "No light version available for $FILENAME"
        fi
    else
        log_debug "Light version $LIGHT_FILENAME already exists, skipping..."
        ((LIGHT_EXISTED_COUNT++))
    fi

    ((PROCESSED_COUNT++))
    update_status # Update the live status line

done <<< "$ICON_URLS"

# --- Final Output ---
# Add a newline after the loop finishes in non-debug mode to move off the status line
if [ "$DEBUG" = false ]; then
    echo "" # Move to the next line
fi

END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log_info "Download process finished at $END_TIME."
log_info "Final Counts - Downloaded: $DOWNLOADED_COUNT | Existed: $EXISTED_COUNT | Light Dl: $LIGHT_DOWNLOADED_COUNT | Light Ex: $LIGHT_EXISTED_COUNT"
log_info "Script finished."
exit 0