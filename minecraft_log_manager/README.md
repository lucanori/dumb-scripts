# Minecraft Server Log Manager

A bash script to manage log files across multiple Minecraft server instances. The script keeps a configurable number of the most recent log files for each server and deletes older ones.

## Features

- Manage log files for multiple Minecraft servers with a single script
- Configure retention settings individually for each server
- Automatically rotate and truncate large screen.log files (configurable line limit)
- Rotate the script's own log file to prevent it from growing indefinitely
- Minimal logging of deletion activities
- Simple configuration file format

## Setup

1. Clone or download this repository/directory.
2. Make the script executable: `chmod +x minecraft_log_manager.sh`
3. Copy the example configuration file:
   ```bash
   cp minecraft_log_manager.conf.example minecraft_log_manager.conf
   ```
4. Edit the new `minecraft_log_manager.conf` file to configure your servers and log paths.
   *Note: `minecraft_log_manager.conf` will be ignored by Git.*

## Configuration (`minecraft_log_manager.conf`)

Edit the `minecraft_log_manager.conf` file (created in the setup step) to set up your servers:

```
# --- Global Settings ---

# Path to the log file for this script's operations.
# Can be an absolute path or relative to where the script is run.
LOG_FILE=./minecraft_log_manager.log

# Maximum number of lines to keep in this script's log file (LOG_FILE).
LOG_MAX_LINES=1000

# Maximum number of lines to keep in each server's screen.log file (if found).
SCREEN_LOG_MAX_LINES=10000

# --- Server Configurations ---
# FORMAT: SERVER_NAME|/path/to/server/logs|number_of_logs_to_keep

# --- Examples ---
# SURVIVAL|/srv/minecraft/survival/logs|30
# CREATIVE|/opt/minecraft_servers/creative/logs|15
```

### Configuration Format

- `LOG_FILE`: Path where the script will write its own operational log.

# Server configurations
# FORMAT: SERVER_NAME|/path/to/server/logs|number_of_logs_to_keep

# Examples:
SURVIVAL|/mnt/user/minecraft/survival/minecraft/logs|30
CREATIVE|/mnt/user/minecraft/creative/minecraft/logs|15
```

### Configuration Format

- `LOG_FILE`: Path where the script will write its log
- `LOG_MAX_LINES`: Maximum number of lines to keep in the log file (default: 1000)
- `SCREEN_LOG_MAX_LINES`: Maximum number of lines to keep in each server's screen.log file (default: 10000)
- Server entries: Each line represents one server with three fields separated by `|`:
  - Server name (for identification in logs)
  - Full path to the server's log directory
  - Number of log files to keep (most recent ones)

## Usage

Run the script manually:

```
./minecraft_log_manager.sh [OPTIONS]
```

### Command-line Options

- `-c, --config FILE`: Use a specific configuration file instead of the default
- `-d, --dry-run`: Show what would be deleted without actually deleting any files
- `-v, --verbose`: Enable verbose output for debugging
- `-h, --help`: Display help information

### Examples

Run with the default configuration:
```
./minecraft_log_manager.sh
```

Run with a custom configuration file:
```
./minecraft_log_manager.sh -c /path/to/custom_config.conf
```

Run in dry-run mode to see what would be deleted:
```
./minecraft_log_manager.sh --dry-run
```

Run with verbose output for debugging:
```
./minecraft_log_manager.sh --verbose
```

Run with both dry-run and verbose modes:
```
./minecraft_log_manager.sh --dry-run --verbose
```

Set up a cron job to run it automatically:
```
# Run daily at 3 AM
0 3 * * * /path/to/minecraft_log_manager.sh
```

## Log Format

The script creates minimal logs, with one line per server when files are deleted:

```
[2025-03-15 06:30:00] Starting Minecraft log management script
[2025-03-15 06:30:01] Deleted 25 log files from server SURVIVAL (/mnt/user/minecraft/survival/minecraft/logs)
[2025-03-15 06:30:02] Minecraft log management script completed