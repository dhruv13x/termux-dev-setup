from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any

def validate_port(port: Any) -> int:
    """Validates that a port is between 1 and 65535."""
    try:
        port = int(port)
    except (ValueError, TypeError):
        raise ValueError("invalid literal for int")

    if not (1 <= port <= 65535):
        raise ValueError("Port must be between 1 and 65535")
    return port

def validate_non_empty(value: str, field_name: str) -> str:
    """Validates that a string is not empty."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    return value

@dataclass
class PostgresConfig:
    port: int = 5432
    data_dir: str = "/var/lib/postgresql/data"
    log_file: str = "/var/log/postgresql/postgresql.log"
    pg_user: str = "postgres"
    host: str = "127.0.0.1"

    def __post_init__(self):
        # Allow environment overrides
        self.data_dir = os.environ.get("PG_DATA", self.data_dir)
        self.log_file = os.environ.get("PG_LOG", self.log_file)
        self.pg_user = os.environ.get("PG_USER", self.pg_user)

        # Validate
        # Note: PostgresConfig doesn't pull port from env by default in the original code,
        # so we validate whatever is in self.port (default or init-provided).
        self.port = validate_port(self.port)
        self.data_dir = validate_non_empty(self.data_dir, "data_dir")
        self.log_file = validate_non_empty(self.log_file, "log_file")
        self.pg_user = validate_non_empty(self.pg_user, "pg_user")
        self.host = validate_non_empty(self.host, "host")

@dataclass
class RedisConfig:
    port: int = 6379
    conf_path: str = "/etc/redis/redis.conf"
    data_dir: str = "/var/lib/redis"
    log_file: str = "/var/log/redis/redis-server.log"
    password: str = ""
    append_only: str = "yes"
    host: str = "127.0.0.1"

    def __post_init__(self):
        # Env overrides
        # We pass the raw string/int to validate_port which handles casting
        self.port = validate_port(os.environ.get("REDIS_PORT", self.port))

        self.conf_path = os.environ.get("REDIS_CONF", self.conf_path)
        self.data_dir = os.environ.get("REDIS_DATA_DIR", self.data_dir)
        self.append_only = os.environ.get("APPENDONLY", self.append_only)

        # Password logic
        env_pass = os.environ.get("REDIS_PASSWORD", "")
        if env_pass:
            self.password = env_pass
        elif not self.password:
            # Try parsing config if no env var and no password provided in init
            path = Path(self.conf_path)
            if path.exists():
                try:
                    with open(path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("requirepass"):
                                parts = line.split()
                                if len(parts) >= 2:
                                    self.password = parts[1]
                except Exception:
                    pass

        # Validate other fields
        self.conf_path = validate_non_empty(self.conf_path, "conf_path")
        self.data_dir = validate_non_empty(self.data_dir, "data_dir")
        self.log_file = validate_non_empty(self.log_file, "log_file")
        self.host = validate_non_empty(self.host, "host")

        if self.append_only not in ["yes", "no"]:
            raise ValueError("append_only must be 'yes' or 'no'")

@dataclass
class OtelConfig:
    metrics_port: int = 8888
    grpc_port: int = 4317
    http_port: int = 4318
    # Default to user's home/otel-config.yaml or similar if not specified
    # Using HOME relative path logic requires os.path.expanduser which is better done in post_init or defaults
    # For now we use a sensible default that the installer uses.
    config_path: str = ""
    otel_bin: str = ""
    log_file: str = ""

    def __post_init__(self):
        base_dir = Path(os.environ.get("BASE_DIR", os.path.expanduser("~")))

        if not self.config_path:
            self.config_path = str(base_dir / "otel-config.yaml")
        if not self.otel_bin:
            self.otel_bin = str(base_dir / "otelcol-contrib")
        if not self.log_file:
            self.log_file = str(base_dir / "otel.log")

        # Env overrides
        self.metrics_port = validate_port(os.environ.get("OTEL_METRICS_PORT", self.metrics_port))
        self.grpc_port = validate_port(os.environ.get("OTEL_GRPC_PORT", self.grpc_port))
        self.http_port = validate_port(os.environ.get("OTEL_HTTP_PORT", self.http_port))

        self.config_path = os.environ.get("OTEL_CONFIG", self.config_path)
        self.otel_bin = os.environ.get("OTEL_BIN", self.otel_bin)
        self.log_file = os.environ.get("OTEL_LOG", self.log_file)

        self.config_path = validate_non_empty(self.config_path, "config_path")
        self.otel_bin = validate_non_empty(self.otel_bin, "otel_bin")
        self.log_file = validate_non_empty(self.log_file, "log_file")

@dataclass
class GCloudConfig:
    keyring_path: str = "/usr/share/keyrings/cloud.google.gpg"
    repo_file: str = "/etc/apt/sources.list.d/google-cloud-sdk.list"
    repo_url: str = "https://packages.cloud.google.com/apt"
    repo_name: str = "cloud-sdk"
    key_url: str = "https://packages.cloud.google.com/apt/doc/apt-key.gpg"

    def __post_init__(self):
        # Allow environment overrides if needed, though rare for these system paths
        self.keyring_path = os.environ.get("GCLOUD_KEYRING_PATH", self.keyring_path)
        self.repo_file = os.environ.get("GCLOUD_REPO_FILE", self.repo_file)

        # Validate
        self.keyring_path = validate_non_empty(self.keyring_path, "keyring_path")
        self.repo_file = validate_non_empty(self.repo_file, "repo_file")
