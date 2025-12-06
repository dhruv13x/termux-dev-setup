import pytest
from unittest.mock import patch, MagicMock, mock_open
from termux_dev_setup import otel
from termux_dev_setup.config import OtelConfig
import os
import shutil

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    base_dir = tmp_path
    monkeypatch.setenv("BASE_DIR", str(base_dir))
    monkeypatch.setenv("OTEL_VERSION", "1.0.0")
    monkeypatch.setenv("OTEL_SHA256", "correct_sha256")
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(base_dir) if p == "~" else p)
    return base_dir

@pytest.fixture(autouse=True)
def mock_external_libs(monkeypatch):
    # Mocking these on the module so that the code uses our mocks
    monkeypatch.setattr(otel, 'urllib', MagicMock())
    monkeypatch.setattr(otel, 'tarfile', MagicMock())
    monkeypatch.setattr(otel, 'shutil', MagicMock())
    monkeypatch.setattr(otel.os, 'walk', MagicMock(return_value=[("/tmp", [], ["otelcol-contrib"])]))

@patch("termux_dev_setup.otel.check_command", return_value=True)
@patch("termux_dev_setup.otel.run_command")
@patch("builtins.open", new_callable=mock_open)
@patch("termux_dev_setup.otel.hashlib.sha256")
@patch("pathlib.Path.chmod")
def test_setup_otel_success_flow(mock_chmod, mock_sha, mock_open_obj, mock_run, mock_check, mock_env, monkeypatch):
    mock_sha.return_value.hexdigest.return_value = "correct_sha256"
    monkeypatch.setattr(otel.shutil, "move", MagicMock())

    otel.setup_otel()

    mock_run.assert_any_call("apt install -y wget curl tar ca-certificates coreutils")
    otel.urllib.request.urlretrieve.assert_called()
    otel.tarfile.open.assert_called()

    otel_bin = str(mock_env / "otelcol-contrib")
    otel_conf = str(mock_env / "otel-config.yaml")
    mock_run.assert_any_call(f"'{otel_bin}' --config '{otel_conf}' validate")

    assert (mock_env / ".bootstrap_done_otel_only").exists()

def test_setup_otel_already_done(mock_env):
    (mock_env / ".bootstrap_done_otel_only").touch()
    with patch("termux_dev_setup.otel.success") as mock_success:
        otel.setup_otel()
        mock_success.assert_called_with("Bootstrap already done (use OTEL_FORCE_UPDATE=1 to force).")

@patch("termux_dev_setup.otel.run_command")
def test_setup_otel_force_update(mock_run, mock_env, monkeypatch):
    monkeypatch.setenv("OTEL_FORCE_UPDATE", "1")
    (mock_env / ".bootstrap_done_otel_only").touch()

    with patch("termux_dev_setup.otel.check_command", return_value=True), \
         patch("termux_dev_setup.otel.hashlib.sha256") as mock_sha, \
         patch("builtins.open", mock_open(read_data=b'')), \
         patch("pathlib.Path.chmod"):

        mock_sha.return_value.hexdigest.return_value = "correct_sha256"
        monkeypatch.setattr(otel.shutil, "move", MagicMock())

        otel.setup_otel()
        assert mock_run.call_count > 0

@patch("termux_dev_setup.otel.check_command", return_value=False)
def test_setup_otel_no_apt(mock_check, mock_env):
    with patch("termux_dev_setup.otel.error") as mock_error:
        otel.setup_otel()
        mock_error.assert_called_with("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")

@patch("termux_dev_setup.otel.check_command", return_value=True)
@patch("termux_dev_setup.otel.run_command", side_effect=[None, Exception("Install failed")])
def test_setup_otel_dep_install_fails(mock_run, mock_check, mock_env):
    with patch("termux_dev_setup.otel.error") as mock_error:
        otel.setup_otel()
        mock_error.assert_called_with("Failed to install dependencies.")

@patch("termux_dev_setup.otel.check_command", return_value=True)
@patch("platform.machine", return_value="unknown_arch")
def test_setup_otel_unknown_arch_warning(mock_machine, mock_check, mock_env, monkeypatch):
    # We need to successfully complete the flow to avoid other errors
    with patch("termux_dev_setup.otel.warning") as mock_warning, \
         patch("termux_dev_setup.otel.run_command"), \
         patch("builtins.open", mock_open(read_data=b'')), \
         patch("termux_dev_setup.otel.hashlib.sha256") as mock_sha, \
         patch("pathlib.Path.chmod"):

        mock_sha.return_value.hexdigest.return_value = "correct_sha256"
        monkeypatch.setattr(otel.shutil, "move", MagicMock())
        otel.setup_otel()
        mock_warning.assert_called_with("Unknown arch 'unknown_arch' - defaulting to linux_amd64")

@patch("termux_dev_setup.otel.check_command", return_value=True)
def test_setup_otel_download_fails(mock_check, mock_env):
    # Patch the mock that is on the module
    otel.urllib.request.urlretrieve.side_effect = Exception("Download error")

    with patch("termux_dev_setup.otel.error") as mock_error, \
         patch("termux_dev_setup.otel.run_command"):
        otel.setup_otel()
        mock_error.assert_called_with("Download failed: Download error", exit_code=4)

@patch("termux_dev_setup.otel.check_command", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data=b"file content")
@patch("termux_dev_setup.otel.hashlib.sha256")
def test_setup_otel_checksum_mismatch(mock_sha, mock_open, mock_check, mock_env):
    mock_sha.return_value.hexdigest.return_value = "wrong_sha256"

    # We need to make sure urlretrieve doesn't fail (it's mocked by fixture)
    otel.urllib.request.urlretrieve.side_effect = None

    with patch("termux_dev_setup.otel.error") as mock_error, \
         patch("termux_dev_setup.otel.run_command"):
        otel.setup_otel()
        mock_error.assert_called_with("Checksum mismatch! Expected correct_sha256, got wrong_sha256", exit_code=3)

@patch("termux_dev_setup.otel.check_command", return_value=True)
def test_setup_otel_extraction_fails(mock_check, mock_env, monkeypatch):
    otel.tarfile.open.side_effect = Exception("Tar error")

    with patch("termux_dev_setup.otel.error") as mock_error, \
         patch("termux_dev_setup.otel.run_command"), \
         patch("builtins.open", mock_open(read_data=b'')), \
         patch("termux_dev_setup.otel.hashlib.sha256") as mock_sha:

        mock_sha.return_value.hexdigest.return_value = "correct_sha256"
        otel.setup_otel()
        mock_error.assert_called_with("Extraction failed: Tar error", exit_code=5)

@patch("termux_dev_setup.otel.check_command", return_value=True)
def test_setup_otel_binary_not_found(mock_check, mock_env, monkeypatch):
    # Reset side effects from other tests
    otel.tarfile.open.side_effect = None
    # Configure os.walk mock
    otel.os.walk.return_value = [("/tmp", [], ["not_the_binary"])]

    with patch("termux_dev_setup.otel.error") as mock_error, \
         patch("termux_dev_setup.otel.run_command"), \
         patch("builtins.open", mock_open(read_data=b'')), \
         patch("termux_dev_setup.otel.hashlib.sha256") as mock_sha:

        mock_sha.return_value.hexdigest.return_value = "correct_sha256"
        otel.setup_otel()
        mock_error.assert_called_with("Could not locate otelcol-contrib inside archive.")

@patch("termux_dev_setup.otel.check_command", return_value=True)
@patch("termux_dev_setup.otel.run_command", side_effect=[None, None, Exception("Validation failed")])
@patch("pathlib.Path.chmod")
def test_setup_otel_validation_fails(mock_chmod, mock_run, mock_check, mock_env, monkeypatch):
    # mocks: apt update, apt install, validate
    with patch("termux_dev_setup.otel.error") as mock_error, \
         patch("builtins.open", mock_open(read_data=b'')), \
         patch("termux_dev_setup.otel.hashlib.sha256") as mock_sha:

        monkeypatch.setattr(otel.shutil, "move", MagicMock())
        mock_sha.return_value.hexdigest.return_value = "correct_sha256"
        otel.tarfile.open.side_effect = None
        # Ensure os.walk finds the binary (reset from previous test)
        otel.os.walk.return_value = [("/tmp", [], ["otelcol-contrib"])]

        otel.setup_otel()
        mock_error.assert_called_with("Config validation failed", exit_code=6)

# --- Service Management Tests ---

@patch("termux_dev_setup.otel.is_port_open", return_value=True)
def test_manage_otel_start_already_running(mock_port, mock_env):
    with patch("termux_dev_setup.otel.success") as mock_success:
        otel.manage_otel("start")
        mock_success.assert_called_with(f"OpenTelemetry Collector is already running (port 8888).")

@patch("termux_dev_setup.otel.is_port_open", return_value=False)
def test_manage_otel_start_no_bin(mock_port, mock_env):
    # Ensure binary does not exist
    if (mock_env / "otelcol-contrib").exists():
        (mock_env / "otelcol-contrib").unlink()

    with patch("termux_dev_setup.otel.error") as mock_error:
        otel.manage_otel("start")
        assert "Binary" in mock_error.call_args[0][0]
        assert "not found" in mock_error.call_args[0][0]

@patch("termux_dev_setup.otel.is_port_open", return_value=False)
def test_manage_otel_start_no_config(mock_port, mock_env):
    (mock_env / "otelcol-contrib").touch()
    if (mock_env / "otel-config.yaml").exists():
        (mock_env / "otel-config.yaml").unlink()

    with patch("termux_dev_setup.otel.error") as mock_error:
        otel.manage_otel("start")
        assert "Config" in mock_error.call_args[0][0]
        assert "not found" in mock_error.call_args[0][0]

@patch("termux_dev_setup.otel.is_port_open")
@patch("termux_dev_setup.otel.run_command")
def test_manage_otel_start_success(mock_run, mock_port, mock_env):
    (mock_env / "otelcol-contrib").touch()
    (mock_env / "otel-config.yaml").touch()

    # is_port_open sequence: False (initially), True (after start)
    mock_port.side_effect = [False, True]

    with patch("termux_dev_setup.otel.success") as mock_success:
        otel.manage_otel("start")
        mock_success.assert_called_with("OpenTelemetry Collector started successfully.")

@patch("termux_dev_setup.otel.is_port_open", return_value=False)
@patch("termux_dev_setup.otel.run_command")
def test_manage_otel_start_timeout(mock_run, mock_port, mock_env):
    (mock_env / "otelcol-contrib").touch()
    (mock_env / "otel-config.yaml").touch()

    with patch("termux_dev_setup.otel.error") as mock_error, \
         patch("time.sleep"):
        otel.manage_otel("start")
        mock_error.assert_called_with("OpenTelemetry Collector failed to start (timeout). Check logs.")

@patch("termux_dev_setup.otel.is_port_open", return_value=False)
def test_manage_otel_stop_already_stopped(mock_port, mock_env):
    with patch("termux_dev_setup.otel.success") as mock_success:
        otel.manage_otel("stop")
        mock_success.assert_called_with("OpenTelemetry Collector stopped.")

@patch("termux_dev_setup.otel.is_port_open")
@patch("termux_dev_setup.otel.run_command")
def test_manage_otel_stop_success(mock_run, mock_port, mock_env):
    # is_port_open sequence: True (initially), False (after pkill)
    mock_port.side_effect = [True, False]

    with patch("termux_dev_setup.otel.success") as mock_success:
        otel.manage_otel("stop")
        mock_success.assert_called_with("OpenTelemetry Collector stopped.")

@patch("termux_dev_setup.otel.is_port_open", return_value=True)
@patch("termux_dev_setup.otel.run_command")
def test_manage_otel_stop_force_kill(mock_run, mock_port, mock_env):
    # is_port_open returns True initially, then True 10 times (timeout loop), then False (after force kill)
    mock_port.side_effect = [True] + [True]*10 + [False]

    with patch("termux_dev_setup.otel.success") as mock_success, \
         patch("time.sleep"):
        otel.manage_otel("stop")
        mock_success.assert_called_with("OpenTelemetry Collector stopped (force kill).")

@patch("termux_dev_setup.otel.OtelService.stop")
@patch("termux_dev_setup.otel.OtelService.start")
def test_manage_otel_restart(mock_start, mock_stop, mock_env):
    with patch("time.sleep"):
        otel.manage_otel("restart")
        mock_stop.assert_called_once()
        mock_start.assert_called_once()

@patch("termux_dev_setup.otel.is_port_open", return_value=True)
def test_manage_otel_status(mock_port, mock_env):
    with patch("termux_dev_setup.otel.console.print") as mock_print:
        otel.manage_otel("status")
        mock_print.assert_any_call("  Status: [bold green]UP[/bold green]")

@patch("termux_dev_setup.otel.socket.create_connection")
def test_is_port_open_true(mock_socket):
    assert otel.is_port_open(80)

@patch("termux_dev_setup.otel.socket.create_connection", side_effect=Exception)
def test_is_port_open_false(mock_socket):
    assert not otel.is_port_open(80)

def test_manage_otel_generate_config_write_fails(mock_env):
    installer = otel.OtelInstaller()
    with patch("builtins.open", side_effect=IOError("Write failed")), \
         patch("termux_dev_setup.otel.error") as mock_error:
        assert installer.generate_config() == False
        mock_error.assert_called()

def test_manage_otel_start_exception(mock_env):
    service = otel.OtelService()
    (mock_env / "otelcol-contrib").touch()
    (mock_env / "otel-config.yaml").touch()

    with patch("termux_dev_setup.otel.is_port_open", return_value=False), \
         patch("termux_dev_setup.otel.run_command", side_effect=Exception("Start failed")), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service.start()
        mock_error.assert_called_with("Failed to start OTEL: Start failed")

def test_manage_otel_stop_exception(mock_env):
    service = otel.OtelService()

    with patch("termux_dev_setup.otel.is_port_open", return_value=True), \
         patch("termux_dev_setup.otel.run_command", side_effect=Exception("Stop failed")), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service.stop()
        mock_error.assert_called_with("Error stopping OTEL: Stop failed")

@patch("termux_dev_setup.otel.is_port_open", return_value=True)
@patch("termux_dev_setup.otel.run_command")
def test_manage_otel_stop_force_kill_fails(mock_run, mock_port, mock_env):
    # Always True means even force kill didn't work
    mock_port.side_effect = [True] + [True]*10 + [True]

    with patch("termux_dev_setup.otel.warning") as mock_warning, \
         patch("time.sleep"):
        otel.manage_otel("stop")
        mock_warning.assert_called_with("Failed to stop OpenTelemetry Collector.")
