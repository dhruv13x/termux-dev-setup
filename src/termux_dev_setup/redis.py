from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
from .config import RedisConfig
import os
import time
import socket
from pathlib import Path

def is_port_open(host="127.0.0.1", port=6379, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

class RedisService:
    def __init__(self, config: RedisConfig = None):
        self.config = config or RedisConfig()

    def is_running(self) -> bool:
        return is_port_open(self.config.host, self.config.port)

    def start(self):
        if self.is_running():
            success(f"Redis is already running on port {self.config.port}.")
            return
        
        conf_path = Path(self.config.conf_path)
        if not conf_path.exists():
            error(f"Config file {conf_path} not found. Run 'tds setup redis' first.")
            return

        info(f"Starting Redis using {conf_path}...")
        
        # Run as redis user
        cmd = f"nohup redis-server '{conf_path}' >/dev/null 2>&1 &"
        start_cmd = ""
        if check_command("runuser"):
            start_cmd = f"runuser -u redis -- bash -c \"{cmd}\""
        else:
            start_cmd = f"su - redis -c \"{cmd}\""
        
        try:
            run_command(start_cmd, shell=True)
            
            # Wait for readiness
            cli_base = f"redis-cli -p {self.config.port}"
            if self.config.password:
                cli_base += f" -a {self.config.password}"

            for _ in range(15):
                try:
                    res = run_command(f"{cli_base} ping", shell=True, check=False, capture_output=True)
                    if res.returncode == 0 and "PONG" in res.stdout:
                         success("Redis started successfully.")
                         return
                except Exception:
                    pass
                time.sleep(1)
            error("Redis failed to start (timeout).")
        except Exception as e:
            error(f"Failed to start Redis: {e}")

    def stop(self):
        if not self.is_running():
            success("Redis is already stopped.")
            return

        info("Stopping Redis...")

        cli_base = f"redis-cli -p {self.config.port}"
        if self.config.password:
            cli_base += f" -a {self.config.password}"

        try:
            res = run_command(f"{cli_base} shutdown", shell=True, check=False, capture_output=True)
            if res.returncode != 0:
                warning(f"Shutdown failed: {res.stderr}")
                warning("Attempting force kill...")
                run_command("pkill redis-server", check=False)
            
            for _ in range(10):
                if not self.is_running():
                    success("Redis stopped.")
                    return
                time.sleep(1)
            warning("Graceful stop failed.")
        except Exception as e:
            error(f"Error stopping Redis: {e}")

    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()

    def status(self):
        up = self.is_running()
        state = "[bold green]UP[/bold green]" if up else "[bold red]DOWN[/bold red]"
        
        console.print(f"  Status: {state}")
        console.print(f"  Config: {self.config.conf_path}")
        console.print(f"  Port: {self.config.port}")
        
        if up:
            # Verify Auth
            cli_base = f"redis-cli -p {self.config.port}"
            if self.config.password:
                cli_base += f" -a {self.config.password}"

            try:
                res = run_command(f"{cli_base} ping", shell=True, check=False, capture_output=True)
                if "PONG" in res.stdout:
                    console.print("  Health: [green]Healthy (PONG)[/green]")
                else:
                     console.print("  Health: [yellow]Unresponsive[/yellow]")
            except Exception:
                console.print("  Health: [red]Check Failed[/red]")
            
            conn_str = f"redis://:{self.config.password}@" if self.config.password else "redis://"
            conn_str += f"127.0.0.1:{self.config.port}/0"
            console.print(f"  URL: {conn_str}")

class RedisInstaller:
    def __init__(self, config: RedisConfig = None):
        self.config = config or RedisConfig()

    def install_packages(self) -> bool:
        if not check_command("redis-server"):
            info("redis-server not found. Installing via apt...")
            run_command("apt update", check=False)
            try:
                run_command("apt install -y redis-server")
                return True
            except Exception:
                error("Failed to install redis-server via apt.")
                return False
        else:
            info("redis-server is already installed.")
            return True

    def ensure_user(self):
        info("Ensuring 'redis' user exists...")
        if not check_command("id redis"):
             if check_command("adduser"):
                 run_command(f"adduser --system --group --home '{self.config.data_dir}' redis", check=False)
             else:
                 warning("Could not create redis user (adduser not found).")

    def setup_directories(self):
        info(f"Setting up data directory: {self.config.data_dir}")
        run_command(f"mkdir -p '{self.config.data_dir}'")
        run_command(f"chown -R redis:redis '{self.config.data_dir}'", check=False)
        run_command(f"chmod 700 '{self.config.data_dir}'")

        conf_parent = Path(self.config.conf_path).parent
        run_command(f"mkdir -p '{conf_parent}'")

        log_parent = Path(self.config.log_file).parent
        run_command(f"mkdir -p {log_parent}")
        run_command(f"chown -R redis:redis {log_parent}", check=False)

    def generate_config(self) -> bool:
        conf_path = Path(self.config.conf_path)
        if conf_path.exists() and not Path(f"{conf_path}.orig").exists():
            run_command(f"cp '{conf_path}' '{conf_path}.orig'")

        info(f"Generating Redis config at {conf_path}...")

        config_content = f"""# Minimal redis.conf generated by tds
bind 127.0.0.1
protected-mode yes
port {self.config.port}
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis.pid
loglevel notice
logfile {self.config.log_file}
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dir {self.config.data_dir}
appendonly {self.config.append_only}
appendfilename "appendonly.aof"
"""
        if self.config.password:
            config_content += f"requirepass {self.config.password}\n"

        try:
            with open(conf_path, "w") as f:
                f.write(config_content)
            return True
        except IOError as e:
            error(f"Failed to write config file: {e}")
            return False

def manage_redis(action: str):
    """
    Manage Redis service (start/stop/status/restart).
    """
    step(f"Redis {action.capitalize()}")

    service = RedisService()

    if action == "start":
        service.start()
    elif action == "stop":
        service.stop()
    elif action == "restart":
        service.restart()
    elif action == "status":
        service.status()

def setup_redis():
    """
    Install and configure Redis for Termux/Proot (Ubuntu).
    """
    step("Redis Setup")

    installer = RedisInstaller()

    # 1. Install
    if not installer.install_packages():
        return

    # 2. Create User
    installer.ensure_user()

    # 3. Directories
    installer.setup_directories()

    # 4. Config
    if not installer.generate_config():
        return

    # 5. Start
    # Ensure env vars match config for the start command
    os.environ["REDIS_PORT"] = str(installer.config.port)
    os.environ["REDIS_CONF"] = installer.config.conf_path
    os.environ["REDIS_PASSWORD"] = installer.config.password

    manage_redis("start")

if __name__ == "__main__":
    with process_lock("redis_setup"):
        setup_redis()