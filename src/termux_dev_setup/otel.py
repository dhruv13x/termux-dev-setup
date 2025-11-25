from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
import os
import time
import platform
import tarfile
import hashlib
from pathlib import Path
import urllib.request
import shutil

def setup_otel():
    """
    Install and configure OpenTelemetry Collector for Termux/Proot (Ubuntu).
    """
    step("OpenTelemetry Collector Setup")

    # 1. Environment & Configuration
    base_dir = Path(os.environ.get("BASE_DIR", os.path.expanduser("~")))
    otel_version = os.environ.get("OTEL_VERSION", "0.137.0")
    otel_bin_name = "otelcol-contrib"
    otel_bin = base_dir / otel_bin_name
    boot_flag = base_dir / ".bootstrap_done_otel_only"
    otel_sha256 = os.environ.get("OTEL_SHA256", "")
    force_update = os.environ.get("OTEL_FORCE_UPDATE", "0") == "1"
    
    # 2. Check Prerequisites
    if not check_command("apt"):
        error("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")

    if boot_flag.exists() and not force_update:
        success("Bootstrap already done (use OTEL_FORCE_UPDATE=1 to force).")
        return

    # 3. Install Dependencies
    info("Updating apt and installing dependencies...")
    run_command("apt update", check=False)
    try:
        run_command("apt install -y wget curl tar ca-certificates coreutils")
    except Exception:
        error("Failed to install dependencies.")

    # 4. Determine Architecture
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

    # 5. Download & Install Binary
    if otel_bin.exists() and not force_update:
        info(f"Existing binary found at {otel_bin}")
    else:
        otel_filename = f"otelcol-contrib_{otel_version}_{otel_arch}.tar.gz"
        otel_url = f"https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v{otel_version}/{otel_filename}"
        
        info(f"Downloading {otel_url}...")
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpd:
            tmp_path = Path(tmpd) / otel_filename
            try:
                urllib.request.urlretrieve(otel_url, tmp_path)
            except Exception as e:
                error(f"Download failed: {e}", exit_code=4)
            
            # Checksum Verification
            if otel_sha256:
                info("Verifying SHA256 checksum...")
                with open(tmp_path, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                if digest != otel_sha256:
                    error(f"Checksum mismatch! Expected {otel_sha256}, got {digest}", exit_code=3)
                success("Checksum OK.")
            
            info("Extracting archive...")
            try:
                with tarfile.open(tmp_path, "r:gz") as tar:
                    tar.extractall(path=tmpd)
            except Exception as e:
                error(f"Extraction failed: {e}", exit_code=5)

            # Find binary
            found = None
            for root, dirs, files in os.walk(tmpd):
                if otel_bin_name in files:
                    found = Path(root) / otel_bin_name
                    break
            
            if not found:
                 error(f"Could not locate {otel_bin_name} inside archive.")

            shutil.move(str(found), str(otel_bin))
            otel_bin.chmod(0o755)
            success(f"Installed collector binary -> {otel_bin}")

    # 6. Generate Configuration
    otel_conf = base_dir / "otel-config.yaml"
    info(f"Generating config at {otel_conf}...")
    
    config_content = """receivers:
  otlp:
    protocols:
      grpc:
      http:

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
                port: 8888
"""
    with open(otel_conf, "w") as f:
        f.write(config_content)

    # 7. Validate Config
    info("Validating config...")
    try:
        run_command(f"'{otel_bin}' --config '{otel_conf}' validate")
        success("Config validated OK")
    except Exception:
        error("Config validation failed", exit_code=6)

    # 8. Generate Management Script (otm.sh)
    # We will generate a Python wrapper instead of bash for consistency, 
    # OR keep the bash script if the user wants a standalone runner.
    # For now, we'll port the bash logic into a python management command later.
    # But per instructions "move them in there correct location then we'll plan to refactore",
    # the user asked to refactor into python. 
    # We will create a 'manager' module later. For now, we just complete the setup.
    
    # Mark bootstrap done
    boot_flag.touch()

    step("Summary")
    console.print(f"  Binary: {otel_bin}")
    console.print(f"  Config: {otel_conf}")
    console.print("  To start, run: tds manage otel start (Coming Soon)")

if __name__ == "__main__":
    with process_lock("otel_setup"):
        setup_otel()
