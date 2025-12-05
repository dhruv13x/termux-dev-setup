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
