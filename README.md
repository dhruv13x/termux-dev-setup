# Termux Dev Setup (tds)

A comprehensive tool to set up and manage a development environment in Termux (Proot/Ubuntu).

## Features

*   **PostgreSQL**: Install, configure, and manage (start/stop/status).
*   **Redis**: Install, configure, and manage (start/stop/status).
*   **OpenTelemetry**: Install and configure the OTEL Collector.
*   **Google Cloud CLI**: Install and configure `gcloud`.

## Installation

From the `tools` directory:

```bash
pip install -e termux_dev_setup
```

## Usage

The tool provides two main commands: `setup` (installation) and `manage` (runtime control).

### Setup Services

```bash
tds setup postgres   # Install PostgreSQL
tds setup redis      # Install Redis
tds setup otel       # Install OpenTelemetry Collector
tds setup gcloud     # Install Google Cloud CLI
```

### Manage Services

Control your running databases easily without remembering complex `pg_ctl` or `redis-server` flags.

```bash
# PostgreSQL
tds manage postgres start
tds manage postgres stop
tds manage postgres status
tds manage postgres restart

# Redis
tds manage redis start
tds manage redis stop
tds manage redis status
tds manage redis restart
```

### Environment Variables

You can customize installation/management via environment variables:

*   **PostgreSQL**: `PG_PORT`, `PG_DATA`, `PG_USER`, `PG_DB`
*   **Redis**: `REDIS_PORT`, `REDIS_DATA_DIR`, `REDIS_PASSWORD`
*   **OTEL**: `OTEL_VERSION`

## Legacy Scripts
Old bash scripts and python managers have been archived to `termux-dev-setup-legacy-scripts.zip` in the tools root.