from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
import os
import time
import socket
from pathlib import Path
import shutil

# Shared constants
DEFAULT_DATA_DIR = "/var/lib/postgresql/data"
DEFAULT_LOG_FILE = "/var/log/postgresql/postgresql.log"
PG_PORT = 5432

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

def is_port_open(host="127.0.0.1", port=PG_PORT, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def manage_postgres(action: str):
    """
    Manage PostgreSQL service (start/stop/status/restart).
    """
    step(f"PostgreSQL {action.capitalize()}")
    
    pg_bin = get_pg_bin()
    if not pg_bin:
        error("PostgreSQL binaries not found. Is it installed?")

    data_dir = os.environ.get("PG_DATA", DEFAULT_DATA_DIR)
    log_file = os.environ.get("PG_LOG", DEFAULT_LOG_FILE)

    pg_ctl = pg_bin / "pg_ctl"

    if action == "start":
        if is_port_open():
            success("PostgreSQL is already running (port open).")
            return

        info(f"Starting PostgreSQL from {data_dir}...")
        cmd = f"'{pg_ctl}' -D '{data_dir}' -l '{log_file}' start"
        try:
            run_as_postgres(cmd)
            # Wait for readiness
            for _ in range(15):
                if is_port_open():
                    success("PostgreSQL started successfully.")
                    return
                time.sleep(1)
            error("PostgreSQL failed to start (timeout). Check logs.")
        except Exception as e:
            error(f"Failed to start PostgreSQL: {e}")

    elif action == "stop":
        if not is_port_open():
            success("PostgreSQL is already stopped.")
            return

        info("Stopping PostgreSQL...")
        cmd = f"'{pg_ctl}' -D '{data_dir}' stop"
        try:
            run_as_postgres(cmd)
            for _ in range(10):
                if not is_port_open():
                    success("PostgreSQL stopped.")
                    return
                time.sleep(1)
            warning("Graceful stop failed or timed out.")
        except Exception:
             warning("pg_ctl stop failed.")

    elif action == "restart":
        manage_postgres("stop")
        time.sleep(1)
        manage_postgres("start")

    elif action == "status":
        up = is_port_open()
        state = "[bold green]UP[/bold green]" if up else "[bold red]DOWN[/bold red]"
        console.print(f"  Status: {state}")
        console.print(f"  Data Dir: {data_dir}")
        console.print(f"  Log File: {log_file}")
        console.print(f"  Port: {PG_PORT}")
        if up:
             console.print(f"  Connection: postgresql://postgres:<PASS>@127.0.0.1:{PG_PORT}/postgres")

def setup_postgres():
    """
    Install and configure PostgreSQL for Termux/Proot (Ubuntu).
    """
    step("PostgreSQL Setup")

    # 1. Check Environment
    if not check_command("apt"):
        error("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")

    # 2. Install Packages
    info("Checking/Installing PostgreSQL packages...")
    run_command("apt update", check=False)
    try:
        run_command("apt install -y postgresql postgresql-contrib util-linux")
    except Exception:
        error("Failed to install PostgreSQL packages via apt.")

    # 3. Locate Binaries
    pg_bin = get_pg_bin()
    if not pg_bin:
         error("Failed to detect PostgreSQL installation after apt install.")
    
    pg_ver_dir = pg_bin.parent
    initdb_path = pg_bin / "initdb"
    info(f"Detected PostgreSQL version: {pg_ver_dir.name}")

    # 4. Setup User
    info("Ensuring 'postgres' user exists...")
    if not check_command("id postgres"):
        if check_command("adduser"):
            run_command("adduser --system --group --home /var/lib/postgresql --shell /bin/bash --no-create-home postgres", check=False)
        elif check_command("useradd"):
            run_command("useradd -r -d /var/lib/postgresql -s /bin/bash -U postgres", check=False)
        else:
            warning("Could not create postgres user. Proceeding if user exists.")

    # 5. Initialize Database
    data_dir = os.environ.get("DATA_DIR", DEFAULT_DATA_DIR)
    log_file = os.environ.get("PG_LOG", DEFAULT_LOG_FILE)
    
    run_command(f"mkdir -p {data_dir}")
    run_command(f"mkdir -p {os.path.dirname(log_file)}")
    run_command(f"chown -R postgres:postgres {data_dir}")
    run_command(f"chown -R postgres:postgres {os.path.dirname(log_file)}")

    if (Path(data_dir) / "PG_VERSION").exists():
        info(f"Database already initialized at {data_dir}")
    else:
        info(f"Initializing database at {data_dir}...")
        cmd = f"'{initdb_path}' -D '{data_dir}'"
        try:
             run_as_postgres(cmd)
             success("initdb finished.")
        except Exception:
             error("initdb failed.")

    # 6. Start Service (Reuse manage logic)
    # We temporarily set env vars for manage() to pick up if needed, 
    # but manage() uses the same defaults/logic.
    os.environ["PG_DATA"] = data_dir
    os.environ["PG_LOG"] = log_file
    manage_postgres("start")

    # 7. Create DB User/Database
    current_user = os.environ.get("USER", "root")
    pg_user = os.environ.get("PG_USER", current_user)
    pg_db = os.environ.get("PG_DB", current_user)
    
    info(f"Creating DB user '{pg_user}' and database '{pg_db}'...")
    
    create_role_cmd = f"'{pg_bin}/createuser' -s {pg_user}"
    run_as_postgres(create_role_cmd, check=False)
    
    create_db_cmd = f"'{pg_bin}/createdb' -O {pg_user} {pg_db}"
    run_as_postgres(create_db_cmd, check=False)

    step("Summary")
    console.print(f"  Version: {pg_ver_dir.name}")
    console.print(f"  Data Dir: {data_dir}")
    console.print(f"  Connection: postgresql://{pg_user}:<PASSWORD>@127.0.0.1:{PG_PORT}/{pg_db}")
    
if __name__ == "__main__":
    with process_lock("postgres_setup"):
        setup_postgres()