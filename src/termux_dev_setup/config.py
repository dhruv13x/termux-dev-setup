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
