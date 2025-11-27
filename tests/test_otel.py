# import pytest
# from unittest.mock import patch, MagicMock, mock_open
# from termux_dev_setup import otel
# import os

# @pytest.fixture
# def mock_env(monkeypatch, tmp_path):
#     base_dir = tmp_path
#     monkeypatch.setenv("BASE_DIR", str(base_dir))
#     monkeypatch.setenv("OTEL_VERSION", "1.0.0")
#     monkeypatch.setenv("OTEL_SHA256", "correct_sha256")
#     monkeypatch.setattr(os.path, 'expanduser', lambda p: str(base_dir) if p == "~" else p)
#     return base_dir

# @pytest.fixture(autouse=True)
# def mock_external_libs(monkeypatch):
#     monkeypatch.setattr(otel, 'urllib', MagicMock())
#     monkeypatch.setattr(otel, 'tarfile', MagicMock())
#     monkeypatch.setattr(otel, 'shutil', MagicMock())
#     monkeypatch.setattr(otel.os, 'walk', MagicMock(return_value=[(str(MagicMock()), [], ["otelcol-contrib"])]))
#     # Mock Path to prevent real filesystem operations
#     monkeypatch.setattr(otel, 'Path', MagicMock())

# @patch("termux_dev_setup.otel.check_command", return_value=True)
# @patch("termux_dev_setup.otel.run_command")
# @patch("builtins.open", new_callable=mock_open, read_data=b"file_content")
# @patch("termux_dev_setup.otel.hashlib.sha256")
# def test_setup_otel_success_flow(mock_sha, mock_open, mock_run, mock_check, mock_env):
#     mock_sha.return_value.hexdigest.return_value = "correct_sha256"
#     otel.Path.return_value.exists.return_value = False # Ensure bootstrap flag doesn't exist
#     otel.setup_otel()
#     mock_run.assert_any_call("apt install -y wget curl tar ca-certificates coreutils")
#     otel.urllib.request.urlretrieve.assert_called()
#     otel.tarfile.open.assert_called()
#     otel.shutil.move.assert_called()
#     mock_run.assert_any_call(f"'{mock_env}/otelcol-contrib' --config '{mock_env}/otel-config.yaml' validate")
#     otel.Path(f"{mock_env}/.bootstrap_done_otel_only").touch.assert_called()

# def test_setup_otel_already_done(mock_env):
#     with patch("termux_dev_setup.otel.success") as mock_success:
#         otel.Path.return_value.exists.return_value = True # Bootstrap flag exists
#         otel.setup_otel()
#         mock_success.assert_called_with("Bootstrap already done (use OTEL_FORCE_UPDATE=1 to force).")

# @patch("termux_dev_setup.otel.run_command")
# def test_setup_otel_force_update(mock_run, mock_env, monkeypatch):
#     monkeypatch.setenv("OTEL_FORCE_UPDATE", "1")
#     otel.Path.return_value.exists.return_value = True # Flag exists, but we force
#     with patch("builtins.open", mock_open(read_data=b'')), patch("termux_dev_setup.otel.hashlib"):
#         otel.setup_otel()
#         assert mock_run.call_count > 0

# @patch("termux_dev_setup.otel.check_command", return_value=False)
# def test_setup_otel_no_apt(mock_check, mock_env):
#     with patch("termux_dev_setup.otel.error") as mock_error:
#         otel.setup_otel()
#         mock_error.assert_called_with("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")

# @patch("termux_dev_setup.otel.run_command", side_effect=[None, Exception("Install failed")])
# def test_setup_otel_dep_install_fails(mock_run, mock_env):
#     with patch("termux_dev_setup.otel.error") as mock_error:
#         otel.setup_otel()
#         mock_error.assert_called_with("Failed to install dependencies.")

# @patch("platform.machine", return_value="unknown_arch")
# def test_setup_otel_unknown_arch_warning(mock_machine, mock_env):
#     with patch("termux_dev_setup.otel.warning") as mock_warning, \
#          patch("termux_dev_setup.otel.run_command"), \
#          patch("builtins.open", mock_open(read_data=b'')), patch("termux_dev_setup.otel.hashlib"):
#         otel.setup_otel()
#         mock_warning.assert_called_with("Unknown arch 'unknown_arch' - defaulting to linux_amd64")

# @patch("urllib.request.urlretrieve", side_effect=Exception("Download error"))
# def test_setup_otel_download_fails(mock_urlretrieve, mock_env):
#     with patch("termux_dev_setup.otel.error") as mock_error, \
#          patch("termux_dev_setup.otel.run_command"):
#         otel.setup_otel()
#         mock_error.assert_called_with("Download failed: Download error", exit_code=4)

# @patch("builtins.open", new_callable=mock_open, read_data=b"file content")
# @patch("termux_dev_setup.otel.hashlib.sha256")
# def test_setup_otel_checksum_mismatch(mock_sha, mock_open, mock_env):
#     mock_sha.return_value.hexdigest.return_value = "wrong_sha256"
#     with patch("termux_dev_setup.otel.error") as mock_error, \
#          patch("termux_dev_setup.otel.run_command"):
#         otel.setup_otel()
#         mock_error.assert_called_with("Checksum mismatch! Expected correct_sha256, got wrong_sha256", exit_code=3)

# @patch("tarfile.open", side_effect=Exception("Tar error"))
# def test_setup_otel_extraction_fails(mock_tar, mock_env):
#     with patch("termux_dev_setup.otel.error") as mock_error, \
#          patch("termux_dev_setup.otel.run_command"), \
#          patch("builtins.open", mock_open(read_data=b'')), patch("termux_dev_setup.otel.hashlib"):
#         otel.setup_otel()
#         mock_error.assert_called_with("Extraction failed: Tar error", exit_code=5)

# @patch("os.walk", return_value=[("/tmp", [], ["not_the_binary"])])
# def test_setup_otel_binary_not_found(mock_walk, mock_env):
#     with patch("termux_dev_setup.otel.error") as mock_error, \
#          patch("termux_dev_setup.otel.run_command"), \
#          patch("builtins.open", mock_open(read_data=b'')), patch("termux_dev_setup.otel.hashlib"):
#         otel.setup_otel()
#         mock_error.assert_called_with("Could not locate otelcol-contrib inside archive.")

# @patch("termux_dev_setup.otel.run_command", side_effect=[None, None, Exception("Validation failed")])
# def test_setup_otel_validation_fails(mock_run, mock_env):
#     with patch("termux_dev_setup.otel.error") as mock_error, \
#          patch("builtins.open", mock_open(read_data=b'')), patch("termux_dev_setup.otel.hashlib"):
#         otel.setup_otel()
#         mock_error.assert_called_with("Config validation failed", exit_code=6)
