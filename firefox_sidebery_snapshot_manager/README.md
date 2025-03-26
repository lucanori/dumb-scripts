# Firefox Sidebery Snapshot Manager

This script helps manage snapshots created by the [Sidebery](https://addons.mozilla.org/en-US/firefox/addon/sidebery/) Firefox extension. It prevents the snapshot directory from growing indefinitely by automatically deleting the oldest snapshots when the total number exceeds a specified limit.

## Features

-   Counts the number of snapshot files in a specified directory.
-   If the count exceeds a defined maximum, it deletes the oldest snapshots until the count is within the limit.
-   Configurable maximum number of files to keep.

## Requirements

-   Bash
-   Standard Unix utilities (`find`, `wc`, `sort`, `head`, `cut`, `rm`)

## Usage

```bash
./sidebery_snapshot_manager.sh <directory_path> [max_files]
```

**Arguments:**

-   `<directory_path>`: (Required) The full path to the directory where Sidebery stores its snapshots.
-   `[max_files]`: (Optional) The maximum number of snapshot files to keep in the directory. Defaults to 100 if not specified.

**Example:**

To manage snapshots in `/path/to/your/sidebery/snapshots` and keep a maximum of 50 files:

```bash
./sidebery_snapshot_manager.sh /path/to/your/sidebery/snapshots 50
```

## Automation

You can run this script periodically using `cron` or `systemd timers` to automate snapshot management.

**Example Cron Job:**

To run the script daily at 3 AM, keeping 100 snapshots in `/home/user/firefox/sidebery_snapshots`:

```crontab
0 3 * * * /path/to/repo/firefox_sidebery_snapshot_manager/sidebery_snapshot_manager.sh /home/user/firefox/sidebery_snapshots 100 >> /var/log/sidebery_manager.log 2>&1
```

Make sure to replace `/path/to/repo/` and `/home/user/firefox/sidebery_snapshots` with the actual paths on your system. Ensure the script has execute permissions (`chmod +x sidebery_snapshot_manager.sh`).