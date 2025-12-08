from .utils.lock import process_lock
from .utils.shell import run_command, check_command
from .config import PostgresConfig
from .views import PostgresView
from .utils.network import is_port_open
from .utils.postgres_utils import get_pg_bin, run_as_postgres
from .service_status import ServiceStatus, ServiceResult
import os
import time
from pathlib import Path

class PostgresService:
    def __init__(self, config: PostgresConfig = None):
        self.config = config or PostgresConfig()
        self.pg_bin = get_pg_bin()

    def is_running(self) -> bool:
        return is_port_open(self.config.host, self.config.port)

    def start(self) -> ServiceResult:
        if not self.pg_bin:
            return ServiceResult(ServiceStatus.MISSING_BINARIES, "PostgreSQL binaries not found. Is it installed?")

        if self.is_running():
            return ServiceResult(ServiceStatus.ALREADY_RUNNING, "PostgreSQL is already running (port open).")

        pg_ctl = self.pg_bin / "pg_ctl"
        cmd = f"'{pg_ctl}' -D '{self.config.data_dir}' -l '{self.config.log_file}' start"

        try:
            run_as_postgres(cmd)
            # Wait for readiness
            for _ in range(15):
                if self.is_running():
                    return ServiceResult(ServiceStatus.RUNNING, "PostgreSQL started successfully.")
                time.sleep(1)
            return ServiceResult(ServiceStatus.TIMEOUT, "PostgreSQL failed to start (timeout). Check logs.")
        except Exception as e:
            return ServiceResult(ServiceStatus.FAILED, f"Failed to start PostgreSQL: {e}")

    def stop(self) -> ServiceResult:
        if not self.pg_bin:
             return ServiceResult(ServiceStatus.MISSING_BINARIES, "PostgreSQL binaries not found.")

        if not self.is_running():
            return ServiceResult(ServiceStatus.ALREADY_STOPPED, "PostgreSQL is already stopped.")

        pg_ctl = self.pg_bin / "pg_ctl"
        cmd = f"'{pg_ctl}' -D '{self.config.data_dir}' stop"
        try:
            run_as_postgres(cmd)
            for _ in range(10):
                if not self.is_running():
                    return ServiceResult(ServiceStatus.STOPPED, "PostgreSQL stopped.")
                time.sleep(1)
            return ServiceResult(ServiceStatus.TIMEOUT, "Graceful stop failed or timed out.")
        except Exception:
             return ServiceResult(ServiceStatus.FAILED, "pg_ctl stop failed.")

    def restart(self):
        self.stop()
        # If stop failed severely, maybe don't start? But usually restart tries best effort.
        # Original logic was just stop() then sleep() then start().
        time.sleep(1)
        return self.start()

    def status(self):
        # Service just returns state, View handles display
        pass

class PostgresInstaller:
    def __init__(self, config: PostgresConfig = None, view: PostgresView = None, version: str = None):
        self.config = config or PostgresConfig()
        self.view = view or PostgresView()
        self.version = version
        # Support legacy DATA_DIR env var for setup if needed
        if "DATA_DIR" in os.environ:
            self.config.data_dir = os.environ["DATA_DIR"]

    def install_packages(self) -> bool:
        if not check_command("apt"):
            self.view.print_error("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")
            return False

        self.view.print_info("Checking/Installing PostgreSQL packages...")

        pkg_name = "postgresql"
        if self.version:
            pkg_name = f"postgresql-{self.version}"

        run_command("apt update", check=False)
        try:
            cmd = f"apt install -y {pkg_name}"
            # If version is not specified, we add contrib. If version is specified,
            # we rely on dependencies or user can manually install extras if needed,
            # or we can try to guess.
            if not self.version:
                cmd += " postgresql-contrib"

            cmd += " util-linux"

            run_command(cmd)
            return True
        except Exception:
            self.view.print_error(f"Failed to install {pkg_name} packages via apt.")
            return False

    def ensure_user(self):
        self.view.print_info("Ensuring 'postgres' user exists...")
        if not check_command("id postgres"):
            if check_command("adduser"):
                run_command("adduser --system --group --home /var/lib/postgresql --shell /bin/bash --no-create-home postgres", check=False)
            elif check_command("useradd"):
                run_command("useradd -r -d /var/lib/postgresql -s /bin/bash -U postgres", check=False)
            else:
                self.view.print_warning("Could not create postgres user. Proceeding if user exists.")

    def init_db(self, pg_bin: Path) -> bool:
        initdb_path = pg_bin / "initdb"
        run_command(f"mkdir -p {self.config.data_dir}")
        run_command(f"mkdir -p {os.path.dirname(self.config.log_file)}")
        run_command(f"chown -R postgres:postgres {self.config.data_dir}")
        run_command(f"chown -R postgres:postgres {os.path.dirname(self.config.log_file)}")

        if (Path(self.config.data_dir) / "PG_VERSION").exists():
            self.view.print_info(f"Database already initialized at {self.config.data_dir}")
            return True

        self.view.print_info(f"Initializing database at {self.config.data_dir}...")
        cmd = f"'{initdb_path}' -D '{self.config.data_dir}'"
        try:
             run_as_postgres(cmd)
             self.view.print_success("initdb finished.")
             return True
        except Exception:
             self.view.print_error("initdb failed.")
             return False

    def setup_db_user(self, pg_bin: Path):
        current_user = os.environ.get("USER", "root")
        pg_user = os.environ.get("PG_USER", current_user)
        pg_db = os.environ.get("PG_DB", current_user)

        self.view.print_info(f"Creating DB user '{pg_user}' and database '{pg_db}'...")

        create_role_cmd = f"'{pg_bin}/createuser' -s {pg_user}"
        run_as_postgres(create_role_cmd, check=False)

        create_db_cmd = f"'{pg_bin}/createdb' -O {pg_user} {pg_db}"
        run_as_postgres(create_db_cmd, check=False)

        return pg_user, pg_db

class PostgresController:
    def __init__(self, service: PostgresService = None, installer: PostgresInstaller = None, view: PostgresView = None, version: str = None):
        self.view = view or PostgresView()
        self.service = service or PostgresService()
        self.installer = installer or PostgresInstaller(view=self.view, version=version)

    def manage(self, action: str):
        self.view.print_step(f"PostgreSQL {action.capitalize()}")

        if action == "start":
            self.view.print_info(f"Starting PostgreSQL from {self.service.config.data_dir}...")
            result = self.service.start()
            if result.status == ServiceStatus.RUNNING:
                self.view.print_success(result.message)
            elif result.status == ServiceStatus.ALREADY_RUNNING:
                self.view.print_success(result.message)
            elif result.status == ServiceStatus.MISSING_BINARIES:
                self.view.print_error(result.message)
            elif result.status in [ServiceStatus.TIMEOUT, ServiceStatus.FAILED]:
                self.view.print_error(result.message)

        elif action == "stop":
            if not self.service.is_running() and self.service.pg_bin:
                 pass
            else:
                 self.view.print_info("Stopping PostgreSQL...")

            result = self.service.stop()
            if result.status == ServiceStatus.STOPPED:
                self.view.print_success(result.message)
            elif result.status == ServiceStatus.ALREADY_STOPPED:
                self.view.print_success(result.message)
            elif result.status == ServiceStatus.MISSING_BINARIES:
                self.view.print_error(result.message)
            elif result.status in [ServiceStatus.TIMEOUT, ServiceStatus.FAILED]:
                self.view.print_warning(result.message)

        elif action == "restart":
            self.view.print_info("Stopping PostgreSQL...")
            stop_res = self.service.stop()
            if stop_res.status == ServiceStatus.STOPPED:
                 self.view.print_success(stop_res.message)
            elif stop_res.status == ServiceStatus.ALREADY_STOPPED:
                 self.view.print_success(stop_res.message)
            else:
                 self.view.print_warning(stop_res.message)

            time.sleep(1)

            self.view.print_info(f"Starting PostgreSQL from {self.service.config.data_dir}...")
            start_res = self.service.start()
            if start_res.status == ServiceStatus.RUNNING:
                 self.view.print_success(start_res.message)
            elif start_res.status == ServiceStatus.ALREADY_RUNNING:
                 self.view.print_success(start_res.message)
            else:
                 self.view.print_error(start_res.message)

        elif action == "status":
            self.view.print_status(self.service.is_running(), self.service.config)

    def setup(self):
        self.view.print_step("PostgreSQL Setup")

        # 1. Install
        if not self.installer.install_packages():
            return

        # 2. Locate Binaries
        # Re-initialize service/pg_bin detection since it might have been installed just now
        self.service.pg_bin = get_pg_bin()
        pg_bin = self.service.pg_bin

        if not pg_bin:
             self.view.print_error("Failed to detect PostgreSQL installation after apt install.")
             return

        pg_ver_dir = pg_bin.parent
        self.view.print_info(f"Detected PostgreSQL version: {pg_ver_dir.name}")

        # 3. Setup User
        self.installer.ensure_user()

        # 4. Init DB
        if not self.installer.init_db(pg_bin):
            return

        # 5. Start Service
        # Pass state via env vars for now as manage() uses Service which reads config which reads env
        # A cleaner way would be to pass config to manage(), but manage() currently instantiates its own service.
        # Since we are inside the controller, we can just call manage directly on self.
        os.environ["PG_DATA"] = self.installer.config.data_dir
        os.environ["PG_LOG"] = self.installer.config.log_file

        # We need to update the service config because manage() uses self.service
        # But PostgresConfig loads from env at init.
        # We can re-init the service or update config manually.
        self.service.config = PostgresConfig() # Re-load config with new env vars
        self.manage("start")

        # 6. Create DB User
        pg_user, pg_db = self.installer.setup_db_user(pg_bin)

        self.view.print_step("Summary")
        self.view.print_status(True, self.installer.config)


def manage_postgres(action: str):
    """
    Manage PostgreSQL service (start/stop/status/restart).
    """
    controller = PostgresController()
    controller.manage(action)

def setup_postgres(version: str = None):
    """
    Install and configure PostgreSQL for Termux/Proot (Ubuntu).

    Args:
        version (str, optional): Specific version to install (e.g., '15').
    """
    controller = PostgresController(version=version)
    controller.setup()
    
if __name__ == "__main__":
    with process_lock("postgres_setup"):
        setup_postgres()
