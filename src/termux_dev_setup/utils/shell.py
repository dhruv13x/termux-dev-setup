import subprocess
import shlex
from .status import error

def run_command(command: str, shell: bool = False, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess:
    """
    Run a shell command safely.
    
    Args:
        command: The command string to run.
        shell: If True, run through the shell (use carefully).
        check: If True, raise/exit on failure.
        capture_output: If True, return stdout/stderr in the result.
    """
    args = command if shell else shlex.split(command)
    
    try:
        result = subprocess.run(
            args,
            shell=shell,
            check=check,
            text=True,
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            # If capturing output, the error might be in stderr
            err_msg = e.stderr.strip() if e.stderr else str(e)
            error(f"Command failed: {command}\nError: {err_msg}", exit_code=e.returncode)

    except FileNotFoundError:
        error(f"Command not found: {args[0] if isinstance(args, list) else args}", exit_code=127)


def check_command(cmd: str) -> bool:
    """Check if a command exists in the PATH."""
    from shutil import which
    return which(cmd) is not None
