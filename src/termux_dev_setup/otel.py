from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
from .config import OtelConfig
import os
import time
import platform
import tarfile
import hashlib
from pathlib import Path
import urllib.request
import shutil
import socket

def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

class OtelService:
    def __init__(self, config: OtelConfig = None):
        self.config = config or OtelConfig()

    def is_running(self) -> bool:
        # Check metrics port as a proxy for running status
        return is_port_open(self.config.metrics_port)

    def start(self):
        if self.is_running():
            success(f"OpenTelemetry Collector is already running (port {self.config.metrics_port}).")
            return

        otel_bin = Path(self.config.otel_bin)
        config_path = Path(self.config.config_path)

        if not otel_bin.exists():
            error(f"Binary {otel_bin} not found. Run 'tds setup otel' first.")
            return

        if not config_path.exists():
            error(f"Config {config_path} not found. Run 'tds setup otel' first.")
            return

        info(f"Starting OpenTelemetry Collector...")

        # Run in background
        cmd = f"nohup '{otel_bin}' --config '{config_path}' > '{self.config.log_file}' 2>&1 &"

        try:
            run_command(cmd, shell=True)

            # Wait for readiness
            for _ in range(10):
                if self.is_running():
                    success("OpenTelemetry Collector started successfully.")
                    return
                time.sleep(1)
            error("OpenTelemetry Collector failed to start (timeout). Check logs.")
        except Exception as e:
            error(f"Failed to start OTEL: {e}")

    def stop(self):
        if not self.is_running():
            success("OpenTelemetry Collector stopped.")
            return

        info("Stopping OpenTelemetry Collector...")

        # Kill by name since we know the binary name
        # A more robust way would be storing PID, but pkill is simple for now
        # assuming unique binary name 'otelcol-contrib' in this environment
        bin_name = Path(self.config.otel_bin).name

        try:
            run_command(f"pkill -f {bin_name}", check=False)

            for _ in range(10):
                if not self.is_running():
                    success("OpenTelemetry Collector stopped.")
                    return
                time.sleep(1)

            # Force kill if needed
            run_command(f"pkill -9 -f {bin_name}", check=False)
            if not self.is_running():
                success("OpenTelemetry Collector stopped (force kill).")
            else:
                 warning("Failed to stop OpenTelemetry Collector.")

        except Exception as e:
            error(f"Error stopping OTEL: {e}")

    def restart(self):
        self.stop()
        time.sleep(1)
        self.start()

    def status(self):
        up = self.is_running()
        state = "[bold green]UP[/bold green]" if up else "[bold red]DOWN[/bold red]"

        console.print(f"  Status: {state}")
        console.print(f"  Binary: {self.config.otel_bin}")
        console.print(f"  Config: {self.config.config_path}")
        console.print(f"  Log:    {self.config.log_file}")
        console.print(f"  Ports:  Metrics={self.config.metrics_port}, gRPC={self.config.grpc_port}, HTTP={self.config.http_port}")

class OtelInstaller:
    def __init__(self, config: OtelConfig = None):
        self.config = config or OtelConfig()
        # Derive some values used in installation
        # Note: In a stricter refactor, we might want these in Config, but they are transient install params.
        self.otel_version = os.environ.get("OTEL_VERSION", "0.137.0")
        self.otel_sha256 = os.environ.get("OTEL_SHA256", "")
        self.force_update = os.environ.get("OTEL_FORCE_UPDATE", "0") == "1"
        self.base_dir = Path(os.path.dirname(self.config.config_path)) # Assume config is in base dir

    def check_prerequisites(self) -> bool:
        if not check_command("apt"):
            error("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")
            return False

        boot_flag = self.base_dir / ".bootstrap_done_otel_only"
        if boot_flag.exists() and not self.force_update:
            success("Bootstrap already done (use OTEL_FORCE_UPDATE=1 to force).")
            return False
        return True

    def install_dependencies(self):
        info("Updating apt and installing dependencies...")
        run_command("apt update", check=False)
        try:
            run_command("apt install -y wget curl tar ca-certificates coreutils")
        except Exception:
            error("Failed to install dependencies.")
            return False
        return True

    def install_binary(self) -> bool:
        otel_bin = Path(self.config.otel_bin)

        if otel_bin.exists() and not self.force_update:
            info(f"Existing binary found at {otel_bin}")
            return True

        # Determine Architecture
        arch_map = {
            "x86_64": "linux_amd64",
            "amd64": "linux_amd64",
            "aarch64": "linux_arm64",
            "arm64": "linux_arm64",
            "armv7l": "linux_armv7",
            "armv7": "linux_armv7",
            "i686": "linux_386",
            "i386": "linux_386"
        }
        sys_arch = platform.machine()
        otel_arch = arch_map.get(sys_arch, "linux_amd64")
        if sys_arch not in arch_map:
            warning(f"Unknown arch '{sys_arch}' - defaulting to {otel_arch}")

        otel_filename = f"otelcol-contrib_{self.otel_version}_{otel_arch}.tar.gz"
        otel_url = f"https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v{self.otel_version}/{otel_filename}"
        
        info(f"Downloading {otel_url}...")
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpd:
            tmp_path = Path(tmpd) / otel_filename
            try:
                urllib.request.urlretrieve(otel_url, tmp_path)
            except Exception as e:
                error(f"Download failed: {e}", exit_code=4)
                return False
            
            # Checksum Verification
            if self.otel_sha256:
                info("Verifying SHA256 checksum...")
                with open(tmp_path, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                if digest != self.otel_sha256:
                    error(f"Checksum mismatch! Expected {self.otel_sha256}, got {digest}", exit_code=3)
                    return False
                success("Checksum OK.")
            
            info("Extracting archive...")
            try:
                with tarfile.open(tmp_path, "r:gz") as tar:
                    tar.extractall(path=tmpd)
            except Exception as e:
                error(f"Extraction failed: {e}", exit_code=5)
                return False

            # Find binary
            found = None
            target_bin_name = "otelcol-contrib"
            for root, dirs, files in os.walk(tmpd):
                if target_bin_name in files:
                    found = Path(root) / target_bin_name
                    break
            
            if not found:
                 error(f"Could not locate {target_bin_name} inside archive.")
                 return False

            shutil.move(str(found), str(otel_bin))
            otel_bin.chmod(0o755)
            success(f"Installed collector binary -> {otel_bin}")
            return True

    def generate_config(self) -> bool:
        otel_conf = Path(self.config.config_path)
        info(f"Generating config at {otel_conf}...")

        # Dynamic config based on ports in config object
        config_content = f"""receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:{self.config.grpc_port}
      http:
        endpoint: 0.0.0.0:{self.config.http_port}

processors:
  batch:

exporters:
  debug:
    verbosity: detailed

extensions:
  health_check:
  pprof:
  zpages:

service:
  extensions: [health_check, pprof, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [debug]
  telemetry:
    metrics:
      level: detailed
      readers:
        - pull:
            exporter:
              prometheus:
                host: 0.0.0.0
                port: {self.config.metrics_port}
"""
        try:
            with open(otel_conf, "w") as f:
                f.write(config_content)
            return True
        except IOError as e:
            error(f"Failed to write config: {e}")
            return False

    def validate_config(self) -> bool:
        info("Validating config...")
        try:
            run_command(f"'{self.config.otel_bin}' --config '{self.config.config_path}' validate")
            success("Config validated OK")
            return True
        except Exception:
            error("Config validation failed", exit_code=6)
            return False

    def finalize(self):
        boot_flag = self.base_dir / ".bootstrap_done_otel_only"
        boot_flag.touch()

        step("Summary")
        console.print(f"  Binary: {self.config.otel_bin}")
        console.print(f"  Config: {self.config.config_path}")
        console.print("  To start, run: tds manage otel start")


def manage_otel(action: str):
    """
    Manage OpenTelemetry Collector service.
    """
    step(f"OpenTelemetry {action.capitalize()}")
    service = OtelService()

    if action == "start":
        service.start()
    elif action == "stop":
        service.stop()
    elif action == "restart":
        service.restart()
    elif action == "status":
        service.status()

def setup_otel():
    """
    Install and configure OpenTelemetry Collector for Termux/Proot (Ubuntu).
    """
    step("OpenTelemetry Collector Setup")
    
    installer = OtelInstaller()

    # 1. Check Prerequisites
    if not installer.check_prerequisites():
        return

    # 2. Install Dependencies
    if not installer.install_dependencies():
        return

    # 3. Install Binary
    if not installer.install_binary():
        return

    # 4. Generate Config
    if not installer.generate_config():
        return

    # 5. Validate Config
    if not installer.validate_config():
        return

    # 6. Finalize
    installer.finalize()

if __name__ == "__main__":
    with process_lock("otel_setup"):
        setup_otel()
