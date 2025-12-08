from .utils.status import console, info, success, error, step
from .utils.lock import process_lock
from .utils.shell import run_command, check_command
from .config import GCloudConfig

class GCloudService:
    """Manages the Google Cloud CLI service."""

    def __init__(self, config: GCloudConfig = None):
        self.config = config or GCloudConfig()

    def is_installed(self) -> bool:
        """Checks if gcloud CLI is installed."""
        return check_command("gcloud")

    def get_version(self) -> str:
        """Returns the installed gcloud version."""
        if not self.is_installed():
            return "Not installed"
        try:
            # Output format: Google Cloud SDK 444.0.0 ...
            output = run_command("gcloud --version", check=False, capture_output=True)
            if output:
                return output.splitlines()[0]
            return "Unknown"
        except Exception:
            return "Unknown"

class GCloudInstaller:
    """Handles installation of Google Cloud CLI."""
    
    def __init__(self, config: GCloudConfig = None):
        self.config = config or GCloudConfig()
        self.service = GCloudService(self.config)

    def install(self, version: str = None):
        """
        Install Google Cloud CLI.

        Args:
            version (str, optional): Specific version to install.
        """
        step("Google Cloud CLI Setup")

        # 1. Check Environment
        if not check_command("apt-get"):
            error("apt-get not found. Ensure you are inside an Ubuntu/Debian proot-distro.")
            return

        # 2. Install Prerequisites
        info("Installing prerequisites...")
        run_command("apt-get update -y", check=False)
        try:
            run_command("apt-get install -y apt-transport-https ca-certificates gnupg curl gnupg2 lsb-release")
        except Exception:
            error("Failed to install prerequisites.")
            return

        # 3. Import Google Cloud Public Key
        info("Importing Google Cloud public key...")
        try:
            # We combine curl and gpg --dearmor
            cmd = f"curl -fsSL {self.config.key_url} | gpg --dearmor -o {self.config.keyring_path} --yes"
            run_command(cmd, shell=True)
        except Exception:
            error("Failed to import Google Cloud key.")
            return

        # 4. Add Repository
        info("Adding Google Cloud SDK repository...")
        repo_line = f"deb [signed-by={self.config.keyring_path}] {self.config.repo_url} {self.config.repo_name} main"
        
        # Check if already exists to avoid duplicates
        try:
            with open(self.config.repo_file, "w") as f:
                f.write(repo_line + "\n")
        except IOError as e:
            error(f"Failed to write repo file: {e}")
            return

        # 5. Install gcloud CLI
        info("Installing google-cloud-cli...")

        pkg_name = "google-cloud-cli"
        if version:
            pkg_name = f"google-cloud-cli={version}-*"
            info(f"Targeting version: {version}")

        run_command("apt-get update -y", check=False)
        try:
            run_command(f"apt-get install -y {pkg_name}")
        except Exception:
            error(f"Failed to install {pkg_name}.")
            return

        # 6. Verification & Init
        if self.service.is_installed():
            success("gcloud CLI installed successfully.")
            run_command("gcloud --version", check=False)

            console.print("")
            info("To initialize, run: gcloud init")

            # We do NOT run 'gcloud init' automatically as it is interactive
        else:
            error("gcloud command not found after installation.")

def setup_gcloud(version: str = None):
    """
    Facade for GCloudInstaller.install().
    """
    with process_lock("gcloud_setup"):
        installer = GCloudInstaller()
        installer.install(version)
