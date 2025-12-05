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

## 📖 About

Why does this exist? Setting up services like PostgreSQL or Redis on a mobile environment can be tricky. `tds` abstracts away the complexity, providing a seamless experience for developers who want to code on the go. Whether you're building a backend API or learning cloud engineering, `tds` prepares your environment so you can focus on writing code.

## 🚀 Quick Start

### Prerequisites

- **Termux** with **Proot-Distro** (Ubuntu recommended) installed.
- **Python 3.8+**
- `pip` (Python Package Installer)

### Installation

Install `tds` directly from the source with a single command:

```bash
pip install .
```

### Usage Example

Get a PostgreSQL database up and running in under a minute:

```bash
# 1. Install and Configure PostgreSQL
tds setup postgres

# 2. Start the Server
tds manage postgres start

# 3. Check Status (Is it running?)
tds manage postgres status

# 4. Connect to your database
# (Connection string provided in output)
```

## ✨ Key Features

- **PostgreSQL Management**: **God Level** control over your database. Install, configure, start, stop, and restart with ease.
- **Redis Support**: Full lifecycle management for Redis, including password protection and persistence settings.
- **OpenTelemetry Management**: Full lifecycle management (start, stop, status) for the OTEL collector.
- **Google Cloud CLI**: Seamless installation of `gcloud` to manage your GCP resources from your phone.
- **Smart Validation**: Built-in checks for ports, configuration paths, and environment variables.
- **Robust Error Handling**: informative error messages to help you debug setup issues quickly.

## ⚙️ Configuration & Advanced Usage

Customize your setup using Environment Variables. `tds` respects these variables during setup and execution.

### Environment Variables

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `PG_PORT` | PostgreSQL listening port | `5432` |
| `PG_DATA` | PostgreSQL data directory | `/var/lib/postgresql/data` |
| `PG_LOG` | PostgreSQL log file path | `/var/log/postgresql/postgresql.log` |
| `PG_USER` | Default PostgreSQL user | `postgres` |
| `PG_DB` | Default database to create | `app` |
| `REDIS_PORT` | Redis listening port | `6379` |
| `REDIS_CONF` | Redis configuration file | `/etc/redis/redis.conf` |
| `REDIS_DATA_DIR` | Redis data directory | `/var/lib/redis` |
| `REDIS_PASSWORD` | Redis password (if any) | `""` (Empty) |
| `APPENDONLY` | Redis Append Only Mode | `yes` |
| `OTEL_VERSION` | OpenTelemetry Collector version | `0.137.0` |

> **Note:** Paths like `/var/lib` refer to the path *inside* your Proot environment.

### CLI Command Reference

| Command | Action | Description |
| :--- | :--- | :--- |
| `tds setup postgres` | Setup | Install & Init PostgreSQL |
| `tds setup redis` | Setup | Install & Configure Redis |
| `tds setup otel` | Setup | Download & Install OTEL Collector |
| `tds setup gcloud` | Setup | Install Google Cloud CLI |
| `tds manage postgres` | `start`, `stop`, `restart`, `status` | Control PostgreSQL Service |
| `tds manage redis` | `start`, `stop`, `restart`, `status` | Control Redis Service |
| `tds manage otel` | `start`, `stop`, `restart`, `status` | Control OpenTelemetry Collector |

## 🏗️ Architecture

`tds` is built with modularity in mind, separating service logic from the CLI interface.

### Directory Structure

```text
src/termux_dev_setup/
├── cli.py            # Entry Point (Argparse logic)
├── config.py         # Configuration Classes & Validation
├── gcloud.py         # Google Cloud Installer
├── otel.py           # OpenTelemetry Installer
├── postgres.py       # PostgreSQL Installer & Manager
├── redis.py          # Redis Installer & Manager
└── utils/
    ├── banner.py     # CLI Visuals
    ├── lock.py       # Process Locking
    ├── shell.py      # Shell Command Wrappers
    └── status.py     # Logging & Output Utilities
```

### Core Logic Flow

1.  **Entry**: `cli.py` parses the command (`setup` or `manage`).
2.  **Configuration**: `config.py` loads defaults and overrides them with Environment Variables.
3.  **Execution**: The specific service module (e.g., `postgres.py`) performs the action.
    *   **Setup**: Checks prerequisites (apt, users), installs packages, and initializes data directories.
    *   **Manage**: Uses process control (like `pg_ctl` or direct binary execution) to handle the service state.
4.  **Feedback**: `utils.status` provides rich, colored output to the user.

## 🗺️ Roadmap

We are constantly evolving! Here is a glimpse of what's next:

*   **Upcoming**:
    *   🔌 **Plugin Architecture**: Add your own services easily.
    *   🧪 **Automated Testing**: More robust integration tests.
    *   📊 **Observability Stack**: Prometheus & Grafana setup.
*   **Completed**:
    *   ✅ Core Services (PG, Redis, OTEL, GCloud)
    *   ✅ Service Lifecycle Management (Start/Stop/Restart)

See [ROADMAP.md](ROADMAP.md) for the detailed vision.

## 🤝 Contributing & License

We welcome contributions! Whether it's a bug fix or a new feature, please check out our [GitHub repository](https://github.com/dhruv13x/termux-dev-setup).

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
