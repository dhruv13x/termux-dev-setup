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
[![Test Coverage](https://img.shields.io/badge/coverage-90%25%2B-brightgreen.svg)](https://github.com/dhruv13x/termux-dev-setup/actions/workflows/test.yml)
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

<!-- Docs -->
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://your-docs-link)

</div>


# termux-dev-setup (tds)

A comprehensive tool to set up and manage a development environment in Termux (Proot/Ubuntu).

[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)](https://github.com/dhruv13x/termux-dev-setup)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/downloads/)

## 📖 About

`tds` is a command-line tool designed to simplify the setup and management of a complete development environment on Termux. It provides a "batteries-included" experience for developers who want to run services like PostgreSQL and Redis without the hassle of manual configuration.

## 🚀 Quick Start

### Prerequisites

- Termux with Proot/Ubuntu
- Python 3.8+
- `pip` for installation

### Installation

Install `tds` with a single command:

```bash
pip install .
```

### Usage Example

Here's how to install and manage PostgreSQL:

```bash
# Install PostgreSQL
tds setup postgres

# Start the PostgreSQL server
tds manage postgres start

# Check the status
tds manage postgres status

# Restart the PostgreSQL server
tds manage postgres restart
```

## ✨ Key Features

- **PostgreSQL**: Install, configure, and manage (**start/stop/restart/status**).
- **Redis**: Install, configure, and manage (**start/stop/restart/status**).
- **OpenTelemetry**: Install and configure the OTEL Collector.
- **Google Cloud CLI**: Install and configure `gcloud`.

## ⚙️ Configuration & Advanced Usage

### Environment Variables

| Variable       | Description                  | Default Value  |
|----------------|------------------------------|----------------|
| `PG_PORT`      | PostgreSQL port              | `5432`         |
| `PG_DATA`      | PostgreSQL data directory    | `~/.tds/pg`    |
| `PG_USER`      | PostgreSQL user              | `admin`        |
| `PG_DB`        | PostgreSQL database          | `app`          |
| `REDIS_PORT`   | Redis port                   | `6379`         |
| `REDIS_DATA_DIR`| Redis data directory       | `~/.tds/redis` |
| `REDIS_PASSWORD`| Redis password               | `""`           |
| `OTEL_VERSION` | OpenTelemetry Collector version | `0.77.0`       |

### CLI Commands

| Command               | Description                             |
|-----------------------|-----------------------------------------|
| `tds setup postgres`  | Install and configure PostgreSQL        |
| `tds setup redis`     | Install and configure Redis             |
| `tds setup otel`      | Install OpenTelemetry Collector         |
| `tds setup gcloud`    | Install Google Cloud CLI                |
| `tds manage postgres [action]` | Manage PostgreSQL (start/stop/restart/status) |
| `tds manage redis [action]`    | Manage Redis (start/stop/restart/status)    |

## 🏗️ Architecture

### Directory Structure

```
src/
└── termux_dev_setup/
    ├── __init__.py
    ├── cli.py
    ├── gcloud.py
    ├── otel.py
    ├── postgres.py
    ├── redis.py
    └── utils/
        ├── banner.py
        └── status.py
```

### Core Logic Flow

The `tds` tool is a single-entrypoint CLI application. The `cli.py` module uses `argparse` to define the command structure (`setup` and `manage`) and their subcommands. Each service (e.g., `postgres.py`, `redis.py`) has its own dedicated module that contains the logic for installation and management. The `utils` directory provides shared functionality, such as displaying the banner and status messages.

## 🗺️ Roadmap

A high-level overview of our future plans. For a more detailed breakdown, please see our [ROADMAP.md](ROADMAP.md) file.

### ✅ Completed

- **Core Services**: PostgreSQL, Redis, OpenTelemetry, and Google Cloud CLI.
- **Service Management**: Full lifecycle support (`start`, `stop`, `status`, and `restart`).

### 🔮 Upcoming

- **More Services**: Support for RabbitMQ, Elasticsearch, and other popular development tools.
- **Enhanced Configuration**: A dedicated configuration file for easier management of settings.
- **Interactive Mode**: A guided setup process for an improved user experience.
- **Automated Testing**: A robust testing framework to ensure stability and reliability.

## 🤝 Contributing & License

Contributions are welcome! Please open an issue or submit a pull request on our [GitHub repository](https://github.com/dhruv13x/termux-dev-setup).

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
