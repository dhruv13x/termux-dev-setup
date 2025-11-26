from unittest.mock import patch, mock_open
import pytest
from termux_dev_setup import gcloud

def test_setup_gcloud_success():
    """
    Tests the successful installation and configuration of gcloud.
    """
    # check_command should return True for apt-get, then True for gcloud at the end.
    with patch("termux_dev_setup.gcloud.check_command", side_effect=[True, True]) as mock_check_command, \
         patch("termux_dev_setup.gcloud.run_command") as mock_run_command, \
         patch("builtins.open", mock_open()) as mock_file:

        gcloud.setup_gcloud()

        # 1. Check for apt-get
        mock_check_command.assert_any_call("apt-get")

        # 2. Prerequisites
        mock_run_command.assert_any_call("apt-get update -y", check=False)
        mock_run_command.assert_any_call("apt-get install -y apt-transport-https ca-certificates gnupg curl gnupg2 lsb-release")

        # 3. Import Key
        keyring_path = "/usr/share/keyrings/cloud.google.gpg"
        mock_run_command.assert_any_call(
            f"curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o {keyring_path} --yes",
            shell=True
        )

        # 4. Add Repository
        repo_file = "/etc/apt/sources.list.d/google-cloud-sdk.list"
        mock_file.assert_called_once_with(repo_file, "w")
        handle = mock_file()
        repo_line = f"deb [signed-by={keyring_path}] https://packages.cloud.google.com/apt cloud-sdk main"
        handle.write.assert_called_once_with(repo_line + "\n")


        # 5. Install gcloud
        mock_run_command.assert_any_call("apt-get update -y", check=False)
        mock_run_command.assert_any_call("apt-get install -y google-cloud-cli")


        # 6. Verification
        mock_check_command.assert_any_call("gcloud")
        mock_run_command.assert_any_call("gcloud --version", check=False)

def test_setup_gcloud_no_apt():
    """
    Tests that setup fails if apt-get is not found.
    """
    with patch("termux_dev_setup.gcloud.check_command", return_value=False) as mock_check_command, \
         patch("termux_dev_setup.gcloud.run_command") as mock_run_command, \
         patch("termux_dev_setup.gcloud.error") as mock_error:
        gcloud.setup_gcloud()

        mock_check_command.assert_called_once_with("apt-get")
        mock_error.assert_called_once_with("apt-get not found. Ensure you are inside an Ubuntu/Debian proot-distro.")
        mock_run_command.assert_not_called()

def test_setup_gcloud_install_fails():
    """
    Tests the case where gcloud is not found after installation.
    """
    # check_command should return True for apt-get, but False for gcloud at the end.
    with patch("termux_dev_setup.gcloud.check_command", side_effect=[True, False]) as mock_check_command, \
         patch("termux_dev_setup.gcloud.run_command"), \
         patch("builtins.open", mock_open()), \
         patch("termux_dev_setup.gcloud.error") as mock_error:

        gcloud.setup_gcloud()
        mock_error.assert_called_with("gcloud command not found after installation.")

def test_setup_gcloud_prereq_install_exception():
    """
    Tests exception handling during prerequisite installation.
    """
    with patch("termux_dev_setup.gcloud.check_command", return_value=True), \
         patch("termux_dev_setup.gcloud.run_command", side_effect=[None, Exception("Install error")]) as mock_run_command, \
         patch("termux_dev_setup.gcloud.error") as mock_error:
        gcloud.setup_gcloud()
        mock_error.assert_called_with("Failed to install prerequisites.")


def test_setup_gcloud_key_import_exception():
    """
    Tests exception handling during key import.
    """
    with patch("termux_dev_setup.gcloud.check_command", return_value=True), \
         patch("termux_dev_setup.gcloud.run_command", side_effect=[None, None, Exception("Key error")]) as mock_run_command, \
         patch("termux_dev_setup.gcloud.error") as mock_error:
        gcloud.setup_gcloud()
        mock_error.assert_called_with("Failed to import Google Cloud key.")


def test_setup_gcloud_repo_write_exception():
    """
    Tests exception handling when writing the repo file.
    """
    with patch("termux_dev_setup.gcloud.check_command", return_value=True), \
         patch("termux_dev_setup.gcloud.run_command"), \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("termux_dev_setup.gcloud.error") as mock_error:
        mock_file.side_effect = IOError("Permission denied")
        gcloud.setup_gcloud()
        mock_error.assert_called_with("Failed to write repo file: Permission denied")


def test_setup_gcloud_cli_install_exception():
    """
    Tests exception handling during gcloud-cli installation.
    """
    with patch("termux_dev_setup.gcloud.check_command", return_value=True), \
         patch("termux_dev_setup.gcloud.run_command", side_effect=[None, None, None, None, Exception("Install error")]) as mock_run_command, \
         patch("builtins.open", mock_open()), \
         patch("termux_dev_setup.gcloud.error") as mock_error:
        gcloud.setup_gcloud()
        mock_error.assert_called_with("Failed to install google-cloud-cli.")
