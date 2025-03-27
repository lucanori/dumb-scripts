# Crowdsec Docker DynDNS IP Whitelister

When using Crowdsec, especially behind a dynamic public IP address, you might encounter alerts triggered by your own traffic. This script provides a solution by automatically updating Crowdsec's IP whitelist based on a Dynamic DNS (DDNS) hostname, specifically designed for Dockerized Crowdsec instances. It also includes optional integration with [Healthchecks.io](https://healthchecks.io/) for monitoring.

This script is an adaptation and enhancement of the original work by [phipzzz/crowdsec-dyndns-ip-whitelister](https://github.com/phipzzz/crowdsec-dyndns-ip-whitelister).

## How does it work

The script performs the following steps:

1.  **Loads Configuration:** Reads settings from a `.env` file located in the same directory.
2.  **Resolves DDNS:** Gets the current public IP address by resolving the DDNS hostname specified in the `.env` file.
3.  **Checks for IP Change:** Compares the resolved IP against the last known IP stored in a local file (path configurable via `.env`).
4.  **Updates Whitelist (if IP changed):**
    *   Generates the necessary YAML content for the whitelist.
    *   Uses `docker exec` to overwrite the whitelist file *inside* the running Crowdsec container (container name and internal path configurable via `.env`).
    *   Updates the local file with the new IP address.
5.  **Restarts Container (Optional):** If configured in the `.env` file (`RESTART_CONTAINER=true`), it restarts the Crowdsec container using `docker restart` to apply the changes immediately. Otherwise, it logs that a manual reload/restart might be needed.
6.  **Pings Healthchecks.io (Optional):** If a `HEALTHCHECKS_URL` is provided in the `.env` file, the script will:
    *   Ping the URL upon successful completion.
    *   Ping the URL appended with `/fail` if a critical error occurs (e.g., DNS resolution failure, failure to update whitelist in container, failure to write local IP file after update).

## Prerequisites

*   Crowdsec running in a Docker container.
*   Docker client installed and configured on the machine running the script.
*   User running the script needs permissions to execute `docker` commands (usually requires being in the `docker` group or running as root).
*   Python 3 installed.
*   Required Python packages: `requests`, `python-dotenv`.
*   Crowdsec whitelist parser installed in your Crowdsec instance:
    `docker exec <your_crowdsec_container_name> cscli parsers install crowdsecurity/whitelists`
*   (Optional) A check set up on [Healthchecks.io](https://healthchecks.io/) to receive pings from this script.

## Configuration

Create a `.env` file in the same directory as the script (`publicIpWhitelister.py`) with the following variables:

```dotenv
# Required: Your Dynamic DNS hostname
DDNS_HOSTNAME=your-dynamic-hostname.example.com

# Required: The name of your CrowdSec Docker container
CROWDSEC_CONTAINER_NAME=crowdsec

# Optional: Set to "true" to restart the CrowdSec container after updating the whitelist (default: false)
RESTART_CONTAINER=false

# Optional: Path to the file storing the last known public IP (default: ./currentIP)
CURRENT_IP_FILE_PATH=./currentIP

# Optional: Path to the whitelist YAML file inside the CrowdSec container (default: /etc/crowdsec/parsers/s02-enrich/publicIpWhitelist.yaml)
WHITELIST_FILE_PATH_IN_CONTAINER=/etc/crowdsec/parsers/s02-enrich/publicIpWhitelist.yaml

# Optional: Healthchecks.io URL to ping on success/failure. Leave blank to disable.
# Example: https://hc-ping.com/your-uuid
HEALTHCHECKS_URL=
```

An example file `.env.example` is provided. Copy it to `.env` and modify the values accordingly.

## How to Use

1.  **Install Python packages:**
    ```bash
    pip install -r requirements.txt
    # or
    python3 -m pip install -r requirements.txt
    ```
2.  **Install Crowdsec Whitelist Parser:** If not already installed, run:
    ```bash
    docker exec <your_crowdsec_container_name> cscli parsers install crowdsecurity/whitelists
    ```
    Replace `<your_crowdsec_container_name>` with the actual name of your container (as set in `CROWDSEC_CONTAINER_NAME` in your `.env` file).
3.  **Configure `.env`:** Copy `.env.example` to `.env` and fill in your `DDNS_HOSTNAME`, `CROWDSEC_CONTAINER_NAME`, and optionally `HEALTHCHECKS_URL`. Adjust other optional variables if needed.
4.  **Set up a Cron Job:** Schedule the script to run periodically (e.g., every 5 minutes). Ensure the cron job runs from the directory containing the script and the `.env` file, or adjust paths accordingly.
    ```crontab
    */5 * * * * cd /path/to/script/directory && /usr/bin/python3 publicIpWhitelister.py >> /var/log/crowdsec_ip_whitelist.log 2>&1
    ```
    *   Replace `/path/to/script/directory` with the actual path.
    *   Replace `/usr/bin/python3` with the correct path to your Python 3 executable if different.
    *   Adjust the log file path `/var/log/crowdsec_ip_whitelist.log` as desired.
    *   The user running the cron job must have permissions to run `docker` commands.
5.  **Verify:**
    *   Check the script's log output (e.g., `/var/log/crowdsec_ip_whitelist.log`) for successful runs or errors.
    *   If using Healthchecks.io, monitor the status of your check there.
    *   After an IP change, verify the whitelist file inside the container:
        ```bash
        docker exec <your_crowdsec_container_name> cat <your_whitelist_path_in_container>
        ```
    *   Verify the whitelist is loaded by Crowdsec:
        ```bash
        docker exec <your_crowdsec_container_name> cscli parsers list | grep publicIpWhitelist
        ```

## Acknowledgements

This script builds upon the original concept and script created by Philipp Z.:
*   **Original Repository:** [phipzzz/crowdsec-dyndns-ip-whitelister](https://github.com/phipzzz/crowdsec-dyndns-ip-whitelister)

## See also

*   [Crowdsec Whitelist Docs](https://docs.crowdsec.net/docs/whitelist/intro)
*   [Healthchecks.io](https://healthchecks.io/)