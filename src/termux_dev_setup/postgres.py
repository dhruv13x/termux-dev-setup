from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
from .config import PostgresConfig
import os
import time
import socket
from pathlib import Path
import shutil

def get_pg_bin() -> Path:
    """Detect PostgreSQL bin directory."""
    try:
        pg_lib = Path("/usr/lib/postgresql")
        versions = sorted([d for d in pg_lib.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda x: int(x.name))
        if not versions:
            return None
        return versions[-1] / "bin"
    except Exception:
        return None

def run_as_postgres(cmd, check=True, capture_output=False):
    """Helper to run command as postgres user."""
    if check_command("runuser"):
        full_cmd = f"runuser -u postgres -- {cmd}"
    else:
        full_cmd = f"su - postgres -c \"{cmd}\""
    return run_command(full_cmd, shell=True, check=check, capture_output=capture_output)

def is_port_open(host="127.0.0.1", port=5432, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

class PostgresService:
    def __init__(self, config: PostgresConfig = None):
        self.config = config or PostgresConfig()
        self.pg_bin = get_pg_bin()

    def is_running(self) -> bool:
        return is_port_open(self.config.host, self.config.port)

    def start(self):
        if not self.pg_bin:
            error("PostgreSQL binaries not found. Is it installed?")
            return

        if self.is_running():
            success("PostgreSQL is already running (port open).")
            return

        info(f"Starting PostgreSQL from {self.config.data_dir}...")
        pg_ctl = self.pg_bin / "pg_ctl"
        cmd = f"'{pg_ctl}' -D '{self.config.data_dir}' -l '{self.config.log_file}' start"

        try:
            run_as_postgres(cmd)
            # Wait for readiness
            for _ in range(15):
                if self.is_running():
                    success("PostgreSQL started successfully.")
                    return
                time.sleep(1)
            error("PostgreSQL failed to start (timeout). Check logs.")
        except Exception as e:
            error(f"Failed to start PostgreSQL: {e}")

    def stop(self):
        if not self.pg_bin:
             error("PostgreSQL binaries not found.")
             return

        if not self.is_running():
            success("PostgreSQL is already stopped.")
            return

        info("Stopping PostgreSQL...")
        pg_ctl = self.pg_bin / "pg_ctl"
        cmd = f"'{pg_ctl}' -D '{self.config.data_dir}' stop"
        try:
            run_as_postgres(cmd)
            for _ in range(10):
                if not self.is_running():
                    success("PostgreSQL stopped.")
                    return
                time.sleep(1)
            warning("Graceful stop failed or timed out.")
        except Exception:
             warning("pg_ctl stop failed.")

    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()

    def status(self):
        up = self.is_running()
        state = "[bold green]UP[/bold green]" if up else "[bold red]DOWN[/bold red]"
        console.print(f"  Status: {state}")
        console.print(f"  Data Dir: {self.config.data_dir}")
        console.print(f"  Log File: {self.config.log_file}")
        console.print(f"  Port: {self.config.port}")
        if up:
             console.print(f"  Connection: postgresql://{self.config.pg_user}:<PASS>@{self.config.host}:{self.config.port}/postgres")

def manage_postgres(action: str):
    """
    Manage PostgreSQL service (start/stop/status/restart).
    """
    step(f"PostgreSQL {action.capitalize()}")

    # Initialize service with config (implicitly handles env vars)
    service = PostgresService()

    if action == "start":
        service.start()
    elif action == "stop":
        service.stop()
    elif action == "restart":
        service.restart()
    elif action == "status":
        service.status()

class PostgresInstaller:
    def __init__(self, config: PostgresConfig = None):
        self.config = config or PostgresConfig()
        # Support legacy DATA_DIR env var for setup if needed
        if "DATA_DIR" in os.environ:
            self.config.data_dir = os.environ["DATA_DIR"]

    def install_packages(self) -> bool:
        if not check_command("apt"):
            error("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")
            return False

        info("Checking/Installing PostgreSQL packages...")
        run_command("apt update", check=False)
        try:
            run_command("apt install -y postgresql postgresql-contrib util-linux")
            return True
        except Exception:
            error("Failed to install PostgreSQL packages via apt.")
            return False

    def ensure_user(self):
        info("Ensuring 'postgres' user exists...")
        if not check_command("id postgres"):
            if check_command("adduser"):
                run_command("adduser --system --group --home /var/lib/postgresql --shell /bin/bash --no-create-home postgres", check=False)
            elif check_command("useradd"):
                run_command("useradd -r -d /var/lib/postgresql -s /bin/bash -U postgres", check=False)
            else:
                warning("Could not create postgres user. Proceeding if user exists.")

    def init_db(self, pg_bin: Path) -> bool:
        initdb_path = pg_bin / "initdb"
        run_command(f"mkdir -p {self.config.data_dir}")
        run_command(f"mkdir -p {os.path.dirname(self.config.log_file)}")
        run_command(f"chown -R postgres:postgres {self.config.data_dir}")
        run_command(f"chown -R postgres:postgres {os.path.dirname(self.config.log_file)}")

        if (Path(self.config.data_dir) / "PG_VERSION").exists():
            info(f"Database already initialized at {self.config.data_dir}")
            return True

        info(f"Initializing database at {self.config.data_dir}...")
        cmd = f"'{initdb_path}' -D '{self.config.data_dir}'"
        try:
             run_as_postgres(cmd)
             success("initdb finished.")
             return True
        except Exception:
             error("initdb failed.")
             return False

    def setup_db_user(self, pg_bin: Path):
        current_user = os.environ.get("USER", "root")
        pg_user = os.environ.get("PG_USER", current_user)
        pg_db = os.environ.get("PG_DB", current_user)

        info(f"Creating DB user '{pg_user}' and database '{pg_db}'...")

        create_role_cmd = f"'{pg_bin}/createuser' -s {pg_user}"
        run_as_postgres(create_role_cmd, check=False)

        create_db_cmd = f"'{pg_bin}/createdb' -O {pg_user} {pg_db}"
        run_as_postgres(create_db_cmd, check=False)

        return pg_user, pg_db

def setup_postgres():
    """
    Install and configure PostgreSQL for Termux/Proot (Ubuntu).
    """
    step("PostgreSQL Setup")

    installer = PostgresInstaller()

    # 1. Install
    if not installer.install_packages():
        return

    # 2. Locate Binaries
    pg_bin = get_pg_bin()
    if not pg_bin:
         error("Failed to detect PostgreSQL installation after apt install.")
         return
    
    pg_ver_dir = pg_bin.parent
    info(f"Detected PostgreSQL version: {pg_ver_dir.name}")

    # 3. Setup User
    installer.ensure_user()

    # 4. Init DB
    if not installer.init_db(pg_bin):
        return

    # 5. Start Service
    # We rely on the Service class now, but need to make sure env vars are respected if set
    # manage_postgres() creates a new service, which creates a new config.
    # To pass state, we might need to rely on env vars or refactor manage_postgres further.
    # For now, sticking to the facade pattern:
    os.environ["PG_DATA"] = installer.config.data_dir
    os.environ["PG_LOG"] = installer.config.log_file
    manage_postgres("start")

    # 6. Create DB User
    pg_user, pg_db = installer.setup_db_user(pg_bin)

    step("Summary")
    console.print(f"  Version: {pg_ver_dir.name}")
    console.print(f"  Data Dir: {installer.config.data_dir}")
    console.print(f"  Connection: postgresql://{pg_user}:<PASSWORD>@127.0.0.1:{installer.config.port}/{pg_db}")
    
if __name__ == "__main__":
    with process_lock("postgres_setup"):
        setup_postgres()