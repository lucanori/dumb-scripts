#!/bin/bash

CONFIG_FILE="minecraft_log_manager.conf"
LOG_FILE=""
LOG_MAX_LINES=1000
SCREEN_LOG_MAX_LINES=10000
DRY_RUN=false
VERBOSE=false

# Function to display usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -c, --config FILE    Use specified configuration file"
    echo "  -d, --dry-run        Show what would be deleted without actually deleting"
    echo "  -v, --verbose        Enable verbose output for debugging"
    echo "  -h, --help           Show this help message"
    exit 1
}

# Parse command line arguments
parse_args() {
    # If no arguments, just return (use defaults)
    if [ $# -eq 0 ]; then
        return
    fi
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--config)
                if [ -z "$2" ] || [[ "$2" == -* ]]; then
                    echo "Error: --config requires a file path argument."
                    show_usage
                fi
                CONFIG_FILE="$2"
                shift 2
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_usage
                ;;
            "")
                # Skip empty arguments
                shift
                ;;
            *)
                echo "Unknown option: $1"
                show_usage
                ;;
        esac
    done
}

# Function for verbose output
verbose_echo() {
    if [ "$VERBOSE" = true ]; then
        echo "[DEBUG] $1"
    fi
}

# Function to read the configuration file
read_config() {
    # Check if the config directory exists
    config_dir=$(dirname "$CONFIG_FILE")
    if [ ! -d "$config_dir" ]; then
        echo "Error: Configuration directory $config_dir does not exist."
        exit 1
    fi
    
    # Check if the config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Configuration file $CONFIG_FILE not found."
        exit 1
    fi
    
    # Check if the config file is readable
    if [ ! -r "$CONFIG_FILE" ]; then
        echo "Error: Configuration file $CONFIG_FILE is not readable. Check permissions."
        exit 1
    fi
    
    echo "Using configuration file: $CONFIG_FILE"

    # Read global settings
    LOG_FILE=$(grep "^LOG_FILE=" "$CONFIG_FILE" | cut -d= -f2)
    
    if [ -z "$LOG_FILE" ]; then
        echo "Error: LOG_FILE not defined in configuration file."
        exit 1
    fi
    
    # Read log rotation settings
    log_max_lines_setting=$(grep "^LOG_MAX_LINES=" "$CONFIG_FILE" | cut -d= -f2)
    if [[ -n "$log_max_lines_setting" && "$log_max_lines_setting" =~ ^[0-9]+$ ]]; then
        LOG_MAX_LINES=$log_max_lines_setting
    fi
    
    # Read screen.log rotation settings
    screen_log_max_lines_setting=$(grep "^SCREEN_LOG_MAX_LINES=" "$CONFIG_FILE" | cut -d= -f2)
    if [[ -n "$screen_log_max_lines_setting" && "$screen_log_max_lines_setting" =~ ^[0-9]+$ ]]; then
        SCREEN_LOG_MAX_LINES=$screen_log_max_lines_setting
    fi
}

# Function to rotate log file if it exceeds the maximum number of lines
rotate_log_file() {
    if [ ! -f "$LOG_FILE" ]; then
        return
    fi
    
    local line_count=$(wc -l < "$LOG_FILE")
    
    if [ "$line_count" -gt "$LOG_MAX_LINES" ]; then
        local excess_lines=$((line_count - LOG_MAX_LINES))
        local temp_file="${LOG_FILE}.tmp"
        
        # Keep only the last LOG_MAX_LINES lines
        tail -n "$LOG_MAX_LINES" "$LOG_FILE" > "$temp_file"
        mv "$temp_file" "$LOG_FILE"
    fi
}

# Function to log messages
log_message() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    # Rotate log file if needed
    rotate_log_file
    
    echo "[$timestamp] $message" >> "$LOG_FILE"
}

# Function to rotate screen.log file if it exists and exceeds the maximum number of lines
rotate_screen_log() {
    local server_path="$1"
    local screen_log_path="${server_path}/screen.log"
    
    if [ ! -f "$screen_log_path" ]; then
        verbose_echo "No screen.log found at $screen_log_path"
        return
    fi
    
    verbose_echo "Found screen.log at $screen_log_path"
    local line_count=$(wc -l < "$screen_log_path")
    verbose_echo "screen.log has $line_count lines"
    
    if [ "$line_count" -gt "$SCREEN_LOG_MAX_LINES" ]; then
        verbose_echo "screen.log exceeds $SCREEN_LOG_MAX_LINES lines, rotating it"
        local temp_file="${screen_log_path}.tmp"
        
        # Keep only the last SCREEN_LOG_MAX_LINES lines
        tail -n "$SCREEN_LOG_MAX_LINES" "$screen_log_path" > "$temp_file"
        mv "$temp_file" "$screen_log_path"
        
        log_message "Rotated screen.log at $screen_log_path (kept last $SCREEN_LOG_MAX_LINES lines out of $line_count)"
        verbose_echo "screen.log rotation complete"
    else
        verbose_echo "screen.log is under the limit of $SCREEN_LOG_MAX_LINES lines, no rotation needed"
    fi
}

# Function to process a server's log directory
process_server() {
    local server_info="$1"
    local server_name=$(echo "$server_info" | cut -d'|' -f1)
    local server_path=$(echo "$server_info" | cut -d'|' -f2)
    local retention=$(echo "$server_info" | cut -d'|' -f3)

    verbose_echo "Processing server: $server_name, path: $server_path, retention: $retention"

    # Validate server path
    if [ ! -d "$server_path" ]; then
        verbose_echo "Error: Directory $server_path for server $server_name does not exist"
        log_message "Error: Directory $server_path for server $server_name does not exist."
        return
    fi
    
    # Check and rotate screen.log if needed
    rotate_screen_log "$server_path"

    # Validate retention number
    if ! [[ "$retention" =~ ^[0-9]+$ ]]; then
        verbose_echo "Error: Invalid retention value for server $server_name: $retention"
        log_message "Error: Invalid retention value for server $server_name: $retention"
        return
    fi

    # Find log files matching the pattern YYYY-MM-DD-N.log.gz
    # Sort by date (newest first) using a more robust sorting approach
    verbose_echo "Searching for log files in $server_path"
    log_files=$(find "$server_path" -maxdepth 1 -name "*.log.gz" | grep -E "[0-9]{4}-[0-9]{2}-[0-9]+-[0-9]+\.log\.gz" | sort -t- -k1,1r -k2,2r -k3,3nr -k4,4nr)
    
    # Count log files
    total_files=$(echo "$log_files" | wc -l)
    verbose_echo "Found $total_files log files for server $server_name"
    
    # If we have more files than the retention limit
    if [ "$total_files" -gt "$retention" ]; then
        # Get files to delete (keep the newest ones based on retention)
        files_to_delete=$(echo "$log_files" | tail -n +$((retention + 1)))
        delete_count=$(echo "$files_to_delete" | wc -l)
        
        verbose_echo "Server $server_name has $total_files log files, retention is $retention, will delete $delete_count files"
        
        if [ "$DRY_RUN" = true ]; then
            # Just log what would be deleted
            log_message "[DRY RUN] Would delete $delete_count log files from server $server_name ($server_path)"
            if [ "$delete_count" -gt 0 ]; then
                echo "Would delete the following files from $server_name:"
                echo "$files_to_delete" | xargs -n1 basename
                
                if [ "$VERBOSE" = true ]; then
                    echo "[DEBUG] Full paths of files that would be deleted:"
                    echo "$files_to_delete"
                fi
            fi
        else
            # Actually delete the files
            verbose_echo "Deleting $delete_count files from server $server_name"
            echo "$files_to_delete" | xargs rm -f
            
            # Log the deletion
            log_message "Deleted $delete_count log files from server $server_name ($server_path)"
        fi
    else
        verbose_echo "Server $server_name has $total_files log files, retention is $retention, no files to delete"
    fi
}

# Main function
main() {
    # Print script information
    echo "Minecraft Log Manager Script"
    echo "============================"
    echo "Script path: $0"
    echo "Current directory: $(pwd)"
    echo "Arguments received: $@"
    echo "============================"
    
    # Parse command line arguments
    parse_args "$@"
    
    verbose_echo "Script started with CONFIG_FILE=$CONFIG_FILE, DRY_RUN=$DRY_RUN, VERBOSE=$VERBOSE"
    
    # Read configuration
    read_config
    
    verbose_echo "Configuration read successfully. LOG_FILE=$LOG_FILE, LOG_MAX_LINES=$LOG_MAX_LINES, SCREEN_LOG_MAX_LINES=$SCREEN_LOG_MAX_LINES"
    
    # Initialize log file if it doesn't exist
    if [ ! -f "$LOG_FILE" ]; then
        verbose_echo "Log file $LOG_FILE does not exist, creating it"
        mkdir -p "$(dirname "$LOG_FILE")"
        touch "$LOG_FILE"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log_message "Starting Minecraft log management script (DRY RUN MODE)"
        echo "Running in dry-run mode. No files will be deleted."
    else
        log_message "Starting Minecraft log management script"
    fi
    
    # Process each server configuration
    verbose_echo "Processing server configurations from $CONFIG_FILE"
    server_count=0
    grep -E "^[^#].*\|.*\|[0-9]+" "$CONFIG_FILE" | while read -r server_info; do
        server_count=$((server_count + 1))
        verbose_echo "Processing server configuration: $server_info"
        process_server "$server_info"
    done
    
    verbose_echo "Processed $server_count server configurations"
    log_message "Minecraft log management script completed"
}

# Run the script
main "$@"