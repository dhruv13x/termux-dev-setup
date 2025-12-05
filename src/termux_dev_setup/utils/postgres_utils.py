from .shell import run_command, check_command
from pathlib import Path

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
