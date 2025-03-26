#!/bin/bash

# Default maximum number of snapshot files to keep
MAX_FILES=100

# Check if a directory path is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <directory_path> [max_files]"
  echo "  <directory_path>: The directory containing Sidebery snapshots."
  echo "  [max_files]: Optional. The maximum number of snapshots to keep (default: $MAX_FILES)."
  exit 1
fi

DIR="$1"

# Check if the directory exists
if [ ! -d "$DIR" ]; then
  echo "Error: Directory '$DIR' not found."
  exit 1
fi

# Override MAX_FILES if provided as a second argument
if [ ! -z "$2" ]; then
  if [[ "$2" =~ ^[0-9]+$ ]]; then
    MAX_FILES=$2
  else
    echo "Error: max_files must be a positive integer."
    exit 1
  fi
fi

echo "Checking directory: $DIR"
echo "Maximum files to keep: $MAX_FILES"

# Count current files in the directory
CURRENT_FILES=$(find "$DIR" -maxdepth 1 -type f | wc -l)
echo "Current files found: $CURRENT_FILES"

# If the number of files exceeds MAX_FILES, start deleting the oldest ones
if [ $CURRENT_FILES -gt $MAX_FILES ]; then
  echo "Exceeded maximum file count. Removing oldest files..."
  while [ $CURRENT_FILES -gt $MAX_FILES ]; do
    # Find the oldest file
    OLDEST_FILE=$(find "$DIR" -maxdepth 1 -type f -printf '%T+ %p\n' | sort | head -n 1 | cut -d ' ' -f2-)

    if [ -z "$OLDEST_FILE" ]; then
        echo "No more files found to delete."
        break
    fi

    # Delete the oldest file
    echo "Removing: $OLDEST_FILE"
    rm "$OLDEST_FILE"

    # Update the current file count
    CURRENT_FILES=$(find "$DIR" -maxdepth 1 -type f | wc -l)
  done
  echo "Finished removing old files. Current file count: $CURRENT_FILES"
else
  echo "File count is within the limit. No files removed."
fi

echo "Snapshot management complete for $DIR."
