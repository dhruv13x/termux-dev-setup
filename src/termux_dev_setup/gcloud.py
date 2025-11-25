from .utils.status import console, info, success, error, warning, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
import os
from pathlib import Path

def setup_gcloud():
    """
    Install and configure Google Cloud CLI for Termux/Proot (Ubuntu).
    """
    step("Google Cloud CLI Setup")

    # 1. Check Environment
    if not check_command("apt-get"):
        error("apt-get not found. Ensure you are inside an Ubuntu/Debian proot-distro.")

    # 2. Install Prerequisites
    info("Installing prerequisites...")
    run_command("apt-get update -y", check=False)
    try:
        run_command("apt-get install -y apt-transport-https ca-certificates gnupg curl gnupg2 lsb-release")
    except Exception:
        error("Failed to install prerequisites.")

    # 3. Import Google Cloud Public Key
    info("Importing Google Cloud public key...")
    keyring_path = "/usr/share/keyrings/cloud.google.gpg"
    try:
        # We combine curl and gpg --dearmor
        # Note: The original script pipes curl to gpg. We can replicate this or use a temp file.
        # Pipe logic in python:
        run_command(f"curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o {keyring_path} --yes", shell=True)
    except Exception:
        error("Failed to import Google Cloud key.")

    # 4. Add Repository
    info("Adding Google Cloud SDK repository...")
    repo_file = "/etc/apt/sources.list.d/google-cloud-sdk.list"
    repo_line = f"deb [signed-by={keyring_path}] https://packages.cloud.google.com/apt cloud-sdk main"
    
    # Check if already exists to avoid duplicates
    try:
        with open(repo_file, "w") as f:
            f.write(repo_line + "\n")
    except IOError as e:
        error(f"Failed to write repo file: {e}")

    # 5. Install gcloud CLI
    info("Installing google-cloud-cli...")
    run_command("apt-get update -y", check=False)
    try:
        run_command("apt-get install -y google-cloud-cli")
    except Exception:
        error("Failed to install google-cloud-cli.")

    # 6. Verification & Init
    if check_command("gcloud"):
        success("gcloud CLI installed successfully.")
        run_command("gcloud --version", check=False)
        
        console.print("")
        info("To initialize, run: gcloud init")
        
        # We do NOT run 'gcloud init' automatically as it is interactive
    else:
        error("gcloud command not found after installation.")

if __name__ == "__main__":
    with process_lock("gcloud_setup"):
        setup_gcloud()
