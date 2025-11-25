from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
import os
import time
import socket
from pathlib import Path

# Shared Constants
DEFAULT_CONF = "/etc/redis/redis.conf"
DEFAULT_DATA_DIR = "/var/lib/redis"
DEFAULT_LOG_FILE = "/var/log/redis/redis-server.log"
DEFAULT_PORT = 6379

def is_port_open(host="127.0.0.1", port=DEFAULT_PORT, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def get_redis_password(conf_path: Path = Path(DEFAULT_CONF)) -> str:
    """Parse requirepass from config or env."""
    # Env takes precedence
    env_pass = os.environ.get("REDIS_PASSWORD", "")
    if env_pass:
        return env_pass
    
    # Parse config
    if conf_path.exists():
        try:
            with open(conf_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("requirepass"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return parts[1]
        except Exception:
            pass
    return ""

def manage_redis(action: str):
    """
    Manage Redis service (start/stop/status/restart).
    """
    step(f"Redis {action.capitalize()}")

    redis_port = int(os.environ.get("REDIS_PORT", DEFAULT_PORT))
    redis_conf = Path(os.environ.get("REDIS_CONF", DEFAULT_CONF))
    redis_pass = get_redis_password(redis_conf)
    
    cli_base = f"redis-cli -p {redis_port}"
    if redis_pass:
        cli_base += f" -a {redis_pass}"

    if action == "start":
        if is_port_open(port=redis_port):
            success(f"Redis is already running on port {redis_port}.")
            return
        
        if not redis_conf.exists():
            error(f"Config file {redis_conf} not found. Run 'tds setup redis' first.")
            
        info(f"Starting Redis using {redis_conf}...")
        
        # Run as redis user
        cmd = f"nohup redis-server '{redis_conf}' >/dev/null 2>&1 &"
        start_cmd = ""
        if check_command("runuser"):
            start_cmd = f"runuser -u redis -- bash -c \"{cmd}\""
        else:
            start_cmd = f"su - redis -c \"{cmd}\""
        
        try:
            run_command(start_cmd, shell=True)
            
            # Wait for readiness
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

    elif action == "stop":
        if not is_port_open(port=redis_port):
            success("Redis is already stopped.")
            return

        info("Stopping Redis...")
        try:
            res = run_command(f"{cli_base} shutdown", shell=True, check=False, capture_output=True)
            if res.returncode != 0:
                warning(f"Shutdown failed: {res.stderr}")
                warning("Attempting force kill...")
                run_command("pkill redis-server", check=False)
            
            for _ in range(10):
                if not is_port_open(port=redis_port):
                    success("Redis stopped.")
                    return
                time.sleep(1)
            warning("Graceful stop failed.")
        except Exception as e:
            error(f"Error stopping Redis: {e}")

    elif action == "restart":
        manage_redis("stop")
        time.sleep(1)
        manage_redis("start")

    elif action == "status":
        up = is_port_open(port=redis_port)
        state = "[bold green]UP[/bold green]" if up else "[bold red]DOWN[/bold red]"
        
        console.print(f"  Status: {state}")
        console.print(f"  Config: {redis_conf}")
        console.print(f"  Port: {redis_port}")
        
        if up:
            # Verify Auth
            try:
                res = run_command(f"{cli_base} ping", shell=True, check=False, capture_output=True)
                if "PONG" in res.stdout:
                    console.print("  Health: [green]Healthy (PONG)[/green]")
                else:
                     console.print("  Health: [yellow]Unresponsive[/yellow]")
            except Exception:
                console.print("  Health: [red]Check Failed[/red]")
            
            conn_str = f"redis://:{redis_pass}@" if redis_pass else "redis://"
            conn_str += f"127.0.0.1:{redis_port}/0"
            console.print(f"  URL: {conn_str}")

def setup_redis():
    """
    Install and configure Redis for Termux/Proot (Ubuntu).
    """
    step("Redis Setup")

    # 1. Configuration
    redis_port = os.environ.get("REDIS_PORT", str(DEFAULT_PORT))
    redis_data_dir = os.environ.get("REDIS_DATA_DIR", DEFAULT_DATA_DIR)
    redis_conf_path = Path(os.environ.get("REDIS_CONF", DEFAULT_CONF))
    redis_password = os.environ.get("REDIS_PASSWORD", "")
    append_only = os.environ.get("APPENDONLY", "yes")

    # 2. Install Redis Server
    if not check_command("redis-server"):
        info("redis-server not found. Installing via apt...")
        run_command("apt update", check=False)
        try:
            run_command("apt install -y redis-server")
        except Exception:
            error("Failed to install redis-server via apt.")
    else:
        info("redis-server is already installed.")

    # 3. Create Redis System User
    info("Ensuring 'redis' user exists...")
    if not check_command("id redis"):
         if check_command("adduser"):
             run_command(f"adduser --system --group --home '{redis_data_dir}' redis", check=False)
         else:
             warning("Could not create redis user (adduser not found).")

    # 4. Directory Setup
    info(f"Setting up data directory: {redis_data_dir}")
    run_command(f"mkdir -p '{redis_data_dir}'")
    run_command(f"chown -R redis:redis '{redis_data_dir}'", check=False)
    run_command(f"chmod 700 '{redis_data_dir}'")
    run_command(f"mkdir -p '{redis_conf_path.parent}'")
    
    # 5. Generate Configuration
    if redis_conf_path.exists() and not Path(f"{redis_conf_path}.orig").exists():
        run_command(f"cp '{redis_conf_path}' '{redis_conf_path}.orig'")

    info(f"Generating Redis config at {redis_conf_path}...")
    
    config_content = f"""# Minimal redis.conf generated by tds
bind 127.0.0.1
protected-mode yes
port {redis_port}
tcp-backlog 511
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dir {redis_data_dir}
appendonly {append_only}
appendfilename "appendonly.aof"
"""
    if redis_password:
        config_content += f"requirepass {redis_password}\n"

    try:
        with open(redis_conf_path, "w") as f:
            f.write(config_content)
    except IOError as e:
        error(f"Failed to write config file: {e}")

    # 6. Setup Log Directory
    run_command("mkdir -p /var/log/redis")
    run_command("chown -R redis:redis /var/log/redis", check=False)

    # 7. Start Redis (Reuse manage logic)
    # Set envs so manage() picks them up
    os.environ["REDIS_PORT"] = redis_port
    os.environ["REDIS_CONF"] = str(redis_conf_path)
    os.environ["REDIS_PASSWORD"] = redis_password
    manage_redis("start")

if __name__ == "__main__":
    with process_lock("redis_setup"):
        setup_redis()