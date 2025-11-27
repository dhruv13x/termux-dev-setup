from dataclasses import dataclass
from pathlib import Path
import os

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
        self.port = int(os.environ.get("REDIS_PORT", self.port))
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
