# Termux Dev Setup (tds)

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
```

## ✨ Key Features

- **PostgreSQL**: Install, configure, and manage (start/stop/status).
- **Redis**: Install, configure, and manage (start/stop/status).
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
| `tds manage postgres [action]` | Manage PostgreSQL (start/stop/status) |
| `tds manage redis [action]`    | Manage Redis (start/stop/status)    |

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

- [ ] Add support for more services (e.g., RabbitMQ, Elasticsearch)
- [ ] Implement a configuration file for easier management of settings
- [ ] Add more management commands (e.g., `logs`, `restart`)

## 🤝 Contributing & License

Contributions are welcome! Please open an issue or submit a pull request on our [GitHub repository](https://github.com/dhruv13x/termux-dev-setup).

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
