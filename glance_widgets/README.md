# Glance Widgets

This directory contains custom widgets for the [Glance](https://github.com/dgl/glance) system monitoring tool.

## Setup

These widgets rely on environment variables being passed to your Glance container for configuration (like API keys and URLs). This avoids hardcoding sensitive information directly into the widget files.

Refer to the Glance documentation and your container setup (e.g., Docker Compose) on how to pass environment variables. Each widget below lists the required variables.

## Widgets

### Jellyfin Active Streams (`jellyfin_active_streams.yml`)

Displays the number of active streams on your Jellyfin server and shows the profile pictures and usernames of users currently streaming.

**Required Environment Variables:**
*   `JELLYFIN_URL`: The base URL of your Jellyfin instance (e.g., `jellyfin.example.com`).
*   `JELLYFIN_API_KEY`: An API key generated within Jellyfin (Admin Dashboard -> API Keys).

### Unraid Stats (`unraid_stats.yml`)

Shows storage usage (Array and Cache), system stats (CPU load/temp, RAM usage), and disk temperatures for an Unraid server.

This widget fetches data from the [unraid-simple-monitoring-api](https://github.com/NebN/unraid-simple-monitoring-api) project. You need to have this API running and accessible from your Glance instance.

**Required Environment Variables:**
*   `UNRAID_IP`: The IP address of the machine running the `unraid-simple-monitoring-api`. The port is assumed to be `24940` as per the API's default.

### OpenRouter Credit Left (`openrouter_credit_left.yml`)

Displays your current credit balance, total usage, and remaining credits on [OpenRouter.ai](https://openrouter.ai/).

**Required Environment Variables:**
*   `OPENROUTER_API_KEY`: Your API key from OpenRouter.