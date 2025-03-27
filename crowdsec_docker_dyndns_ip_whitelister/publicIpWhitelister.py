import os
import socket
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import sys
import requests

load_dotenv()
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

DDNS_HOSTNAME = os.getenv('DDNS_HOSTNAME')
CROWDSEC_CONTAINER_NAME = os.getenv('CROWDSEC_CONTAINER_NAME')
RESTART_CONTAINER = os.getenv('RESTART_CONTAINER', 'false').lower() == 'true'
CURRENT_IP_FILE_PATH = os.getenv('CURRENT_IP_FILE_PATH', './currentIP')
WHITELIST_FILE_PATH_IN_CONTAINER = os.getenv(
    'WHITELIST_FILE_PATH_IN_CONTAINER',
    '/etc/crowdsec/parsers/s02-enrich/publicIpWhitelist.yaml'
)
HEALTHCHECKS_URL = os.getenv('HEALTHCHECKS_URL')

if not DDNS_HOSTNAME:
    print(f"{timestamp}: Error: DDNS_HOSTNAME environment variable not set.", file=sys.stderr)
    if HEALTHCHECKS_URL:
        requests.get(f"{HEALTHCHECKS_URL}/fail", timeout=10)
    sys.exit(1)
if not CROWDSEC_CONTAINER_NAME:
    print(f"{timestamp}: Error: CROWDSEC_CONTAINER_NAME environment variable not set.", file=sys.stderr)
    if HEALTHCHECKS_URL:
        requests.get(f"{HEALTHCHECKS_URL}/fail", timeout=10)
    sys.exit(1)

def ping_healthchecks(url, status="success"):
    """Pings the Healthchecks.io URL."""
    if not url:
        return

    target_url = url if status == "success" else f"{url}/fail"
    try:
        response = requests.get(target_url, timeout=10)
        response.raise_for_status()
        print(f"{timestamp}: Successfully pinged Healthchecks.io ({status}) at {target_url}")
    except requests.exceptions.RequestException as e:
        print(f"{timestamp}: Warning: Failed to ping Healthchecks.io ({status}) at {target_url}: {e}", file=sys.stderr)
    except Exception as e:
        print(f"{timestamp}: Warning: An unexpected error occurred while pinging Healthchecks.io: {e}", file=sys.stderr)


def get_ip_from_ddns(hostname):
    try:
        ip_address = socket.gethostbyname(hostname)
        print(f"{timestamp}: Successfully resolved {hostname} to {ip_address}")
        return ip_address
    except socket.gaierror as e:
        print(f"{timestamp}: Error resolving DNS for {hostname}: {e}", file=sys.stderr)
        ping_healthchecks(HEALTHCHECKS_URL, "fail")
        return None
    except Exception as e:
        print(f"{timestamp}: An unexpected error occurred during DNS resolution: {e}", file=sys.stderr)
        ping_healthchecks(HEALTHCHECKS_URL, "fail")
        return None

def read_from_file(filename):
    try:
        if not os.path.exists(filename):
             with open(filename, 'w') as file:
                 file.write("")
             print(f"{timestamp}: File {filename} did not exist and was created.")
             return ""
        with open(filename, 'r') as file:
            content = file.read().strip()
            return content
    except Exception as e:
        print(f"{timestamp}: Error while reading the file ({filename}): {e}", file=sys.stderr)
        ping_healthchecks(HEALTHCHECKS_URL, "fail")
        return None

def write_to_file(filename, content):
    try:
        with open(filename, 'w') as file:
            file.write(content)
        print(f"{timestamp}: File {filename} has been written successfully.")
        return True
    except Exception as e:
        print(f"{timestamp}: Error while writing the file ({filename}): {e}", file=sys.stderr)
        return False

def update_whitelist_in_container(container_name, file_path, content):
    command = [
        "docker", "exec", "-i", container_name,
        "sh", "-c", f"cat > \"{file_path}\""
    ]
    try:
        result = subprocess.run(command, input=content, text=True, check=True, capture_output=True)
        print(f"{timestamp}: Successfully updated whitelist file {file_path} in container {container_name}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{timestamp}: Error executing docker command: {' '.join(command)}", file=sys.stderr)
        print(f"{timestamp}: Return code: {e.returncode}", file=sys.stderr)
        print(f"{timestamp}: Stderr: {e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"{timestamp}: An unexpected error occurred during docker exec: {e}", file=sys.stderr)
        return False

def apply_crowdsec_changes(container_name, restart_flag):
    if restart_flag:
        command = ["docker", "restart", container_name]
        try:
            print(f"{timestamp}: Restarting container {container_name}...")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"{timestamp}: Container {container_name} restarted successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"{timestamp}: Error restarting container {container_name}: {' '.join(command)}", file=sys.stderr)
            print(f"{timestamp}: Return code: {e.returncode}", file=sys.stderr)
            print(f"{timestamp}: Stderr: {e.stderr}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"{timestamp}: An unexpected error occurred during docker restart: {e}", file=sys.stderr)
            return False
    else:
        print(f"{timestamp}: Container restart is disabled (RESTART_CONTAINER=false). Manual reload/restart might be needed.")
        return True

current_ip = get_ip_from_ddns(DDNS_HOSTNAME)

if current_ip is None:
    sys.exit(1)

last_known_ip = read_from_file(CURRENT_IP_FILE_PATH)

if last_known_ip is None:
     sys.exit(1)

script_successful = True

if last_known_ip != current_ip:
    print(f"{timestamp}: Public IP has changed from {last_known_ip or 'None'} to {current_ip}. Updating whitelist.")

    whitelists_file_content = f"""name: lucanori/publicIpWhitelist
description: "Whitelist events from public IPv4 address"
whitelist:
  reason: "My public IP (dynamic)"
  ip:
    - "{current_ip}"
"""

    if update_whitelist_in_container(CROWDSEC_CONTAINER_NAME, WHITELIST_FILE_PATH_IN_CONTAINER, whitelists_file_content):
        if write_to_file(CURRENT_IP_FILE_PATH, current_ip):
            if not apply_crowdsec_changes(CROWDSEC_CONTAINER_NAME, RESTART_CONTAINER):
                 print(f"{timestamp}: Warning: Failed to apply changes to CrowdSec container after IP update.", file=sys.stderr)
        else:
            print(f"{timestamp}: Critical Error: Updated whitelist in container but failed to write new IP to {CURRENT_IP_FILE_PATH}. State is inconsistent.", file=sys.stderr)
            ping_healthchecks(HEALTHCHECKS_URL, "fail")
            script_successful = False
            sys.exit(1)
    else:
        print(f"{timestamp}: Critical Error: Failed to update whitelist file in container {CROWDSEC_CONTAINER_NAME}.", file=sys.stderr)
        ping_healthchecks(HEALTHCHECKS_URL, "fail")
        script_successful = False
        sys.exit(1)

else:
    print(f"{timestamp}: IP address ({current_ip}) hasn't changed.")

if script_successful:
    ping_healthchecks(HEALTHCHECKS_URL, "success")

print(f"{timestamp}: Script finished.")