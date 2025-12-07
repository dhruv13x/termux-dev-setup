<div align="center">
  <img src="https://raw.githubusercontent.com/dhruv13x/termux-dev-setup/main/termux-dev-setup_logo.png" alt="termux-dev-setup logo" width="200"/>
</div>

<div align="center">

<!-- Package Info -->
[![PyPI version](https://img.shields.io/pypi/v/termux-dev-setup.svg)](https://pypi.org/project/termux-dev-setup/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
![Wheel](https://img.shields.io/pypi/wheel/termux-dev-setup.svg)
[![Release](https://img.shields.io/badge/release-PyPI-blue)](https://pypi.org/project/termux-dev-setup/)

<!-- Build & Quality -->
[![Build status](https://github.com/dhruv13x/termux-dev-setup/actions/workflows/publish.yml/badge.svg)](https://github.com/dhruv13x/termux-dev-setup/actions/workflows/publish.yml)
[![Codecov](https://codecov.io/gh/dhruv13x/termux-dev-setup/graph/badge.svg)](https://codecov.io/gh/dhruv13x/termux-dev-setup)
[![Test Coverage](https://img.shields.io/badge/coverage-95%25%2B-brightgreen.svg)](https://github.com/dhruv13x/termux-dev-setup/actions/workflows/test.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/linting-ruff-yellow.svg)](https://github.com/astral-sh/ruff)
![Security](https://img.shields.io/badge/security-CodeQL-blue.svg)

<!-- Usage -->
![Downloads](https://img.shields.io/pypi/dm/termux-dev-setup.svg)
[![PyPI Downloads](https://img.shields.io/pypi/dm/termux-dev-setup.svg)](https://pypistats.org/packages/termux-dev-setup)
![OS](https://img.shields.io/badge/os-Linux%20%7C%20macOS%20%7C%20Windows-blue.svg)
[![Python Versions](https://img.shields.io/pypi/pyversions/termux-dev-setup.svg)](https://pypi.org/project/termux-dev-setup/)

<!-- License -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

# termux-dev-setup (tds)

**Your "Batteries Included" Development Environment for Termux.**

`tds` is a powerful CLI tool designed to effortlessly set up and manage a production-grade development environment inside Termux (Proot/Ubuntu). Forget manual configuration files and permission headaches—get your database, cache, and cloud tools running in seconds.

## ⚡ Quick Start

### Prerequisites
*   **Termux** with **Proot-Distro** (Ubuntu recommended).
*   **Python 3.8+** installed.
*   Basic knowledge of terminal operations.

### Installation

Install `tds` directly from the source with a single command:

```bash
pip install .
```

*Or via PyPI (Recommended for users):*

```bash
pip install termux-dev-setup
```

### Run

Launch the interactive wizard to get started immediately:

```bash
tds --interactive
```

### Demo

Get a PostgreSQL database up and running in under a minute:

```bash
# 1. Install and Configure PostgreSQL
tds setup postgres

# 2. Start the Server
tds manage postgres start

# 3. Check Status
tds manage postgres status
```

## ✨ Features

### 💎 Core Services
*   **PostgreSQL**: Production-ready setup with `pg_ctl`. Manage users, databases, and logs effortlessly.
*   **Redis**: Secure, persistent cache with full lifecycle management. Includes password protection and persistence settings.
*   **OpenTelemetry**: Observability out-of-the-box. Install and manage the OTEL Collector for metrics and traces.
*   **Google Cloud CLI**: Seamless installation of `gcloud` to manage your GCP resources from your pocket.

### 🚀 Performance & UX
*   **Interactive Mode**: A user-friendly wizard (`tds -i`) guides you through setup without memorizing flags.
*   **Smart Validation**: Built-in checks for ports, configuration paths, and environment variables prevent errors before they happen.
*   **Version Control**: Specify exactly which version of a service you need (e.g., `tds setup postgres --version 15`).

### 🛡️ Security
*   **Secure Defaults**: Redis is configured with protected mode and password support.
*   **Non-Root Execution**: Services run as the current user, avoiding dangerous root permissions in the container.

## 🛠️ Configuration

Customize your setup using Environment Variables. `tds` respects these variables during setup and execution, allowing for flexible deployments.

### Environment Variables

| Variable | Description | Default Value | Required |
| :--- | :--- | :--- | :--- |
| `PG_PORT` | PostgreSQL listening port | `5432` | No |
| `PG_DATA` | PostgreSQL data directory | `/var/lib/postgresql/data` | No |
| `PG_LOG` | PostgreSQL log file path | `/var/log/postgresql/postgresql.log` | No |
| `PG_USER` | Default PostgreSQL user | `postgres` | No |
| `REDIS_PORT` | Redis listening port | `6379` | No |
| `REDIS_CONF` | Redis configuration file | `/etc/redis/redis.conf` | No |
| `REDIS_DATA_DIR` | Redis data directory | `/var/lib/redis` | No |
| `REDIS_PASSWORD` | Redis password | `""` (Empty) | No |
| `APPENDONLY` | Redis Append Only Mode | `yes` | No |
| `OTEL_METRICS_PORT` | OTEL Metrics Port | `8888` | No |
| `OTEL_GRPC_PORT` | OTEL gRPC Port | `4317` | No |
| `OTEL_HTTP_PORT` | OTEL HTTP Port | `4318` | No |
| `OTEL_CONFIG` | OTEL Config Path | `~/otel-config.yaml` | No |

### CLI Arguments

| Flag/Command | Description | Example |
| :--- | :--- | :--- |
| `--interactive`, `-i` | Launch the interactive setup wizard. | `tds -i` |
| `setup [service]` | Install and configure a service. | `tds setup postgres` |
| `manage [service] [action]` | Control service state (start/stop/restart/status). | `tds manage redis start` |
| `--version` | Specify a version during setup. | `tds setup postgres --version 15` |

## 🏗️ Architecture

`tds` follows a modular architecture, strictly separating the Command Line Interface (CLI) from the core business logic and configuration.

### Directory Tree

```text
src/termux_dev_setup/
├── cli.py            # Entry Point: Parses arguments & routes commands
├── config.py         # Configuration: Dataclasses & Env Var Validation
├── errors.py         # Error Handling: Custom TDSError hierarchy
├── gcloud.py         # Module: Google Cloud Installer
├── interactive.py    # UI: Interactive Wizard Logic
├── otel.py           # Module: OpenTelemetry Installer & Manager
├── postgres.py       # Module: PostgreSQL Installer & Manager
├── redis.py          # Module: Redis Installer & Manager
├── service_status.py # Logic: Service health checking
├── views.py          # UI: Rich library views
└── utils/
    ├── banner.py     # UI: CLI ASCII Art & Banner
    └── status.py     # UI: Logging, Success/Error styling
```

### Data Flow
1.  **User Input**: `cli.py` receives the command or triggers `interactive.py`.
2.  **Configuration**: `config.py` loads defaults and overrides with Environment Variables.
3.  **Validation**: Ports and paths are validated before any action is taken.
4.  **Execution**: The respective module (e.g., `redis.py`) executes the requested action (Setup or Manage).
5.  **Feedback**: `utils.status` renders the result to the console using formatted output.

## 🐞 Troubleshooting

### Common Issues

| Error Message | Possible Cause | Solution |
| :--- | :--- | :--- |
| `Port must be between 1 and 65535` | Invalid port number in Env Vars. | Check `PG_PORT` or `REDIS_PORT`. |
| `Permission denied` | Trying to write to a protected directory. | Ensure you are running in Proot or use user-writable paths. |
| `Service failed to start` | Port conflict or bad config. | Check if another service is using the port. Check logs. |
| `command not found` after install | Path issue. | Ensure Python scripts are in your `$PATH`. Restart shell. |

### Debugging
If a service fails to start, check the specific log files defined in your configuration:
*   **Postgres**: `/var/log/postgresql/postgresql.log` (default)
*   **Redis**: `/var/log/redis/redis-server.log` (default)
*   **OTEL**: `~/otel.log` (default)

## 🤝 Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Dev Setup
1.  Clone the repository.
2.  Install dependencies: `pip install .`
3.  Run tests: `pytest`
4.  Lint code: `ruff check .`

## 🗺️ Roadmap

We are constantly improving `tds`. Here is a snapshot of our upcoming goals:

*   **Phase 1 (Completed)**: Core Services (PG, Redis, OTEL, GCloud), Basic Management.
*   **Phase 2 (Current)**: Interactive Setup, Version Management.
*   **Phase 3 (Upcoming)**: Plugin Architecture, Database Integrations (MySQL/Mongo), Observability Stack.
*   **Phase 4 (Vision)**: AI-Powered Tuning, Remote Tunnels.

See [ROADMAP.md](ROADMAP.md) for the full detailed vision.
