import pytest
from unittest.mock import patch, MagicMock, mock_open
from termux_dev_setup import otel
from termux_dev_setup.otel import OtelService, manage_otel
import os
import shutil
from pathlib import Path

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    base_dir = tmp_path
    monkeypatch.setenv("BASE_DIR", str(base_dir))
    monkeypatch.setenv("OTEL_VERSION", "2.0.1")
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

@patch("termux_dev_setup.otel.OtelConfig")
def test_otel_service_is_running(mock_config_class):
    mock_config = mock_config_class.return_value
    mock_config.metrics_port = 8888

    with patch("termux_dev_setup.otel.is_port_open", return_value=True) as mock_port:
        service = OtelService()
        assert service.is_running() is True
        mock_port.assert_called_with(8888)

    with patch("termux_dev_setup.otel.is_port_open", return_value=False):
        service = OtelService()
        assert service.is_running() is False

@patch("termux_dev_setup.otel.OtelConfig")
@patch("pathlib.Path.exists")
def test_otel_service_start_already_running(mock_exists, mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=True), \
         patch("termux_dev_setup.otel.success") as mock_success:
        service = OtelService()
        service.start()
        mock_success.assert_called()

@patch("termux_dev_setup.otel.OtelConfig")
@patch("pathlib.Path.exists")
def test_otel_service_start_missing_bin(mock_exists, mock_config_class):
    mock_exists.return_value = False # Binary not found
    with patch.object(OtelService, 'is_running', return_value=False), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service = OtelService()
        service.start()
        mock_error.assert_called()

@patch("termux_dev_setup.otel.OtelConfig")
@patch("pathlib.Path.exists", side_effect=[True, False]) # Bin exists, Config missing
def test_otel_service_start_missing_config(mock_exists, mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=False), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service = OtelService()
        service.start()
        mock_error.assert_called()

@patch("termux_dev_setup.otel.OtelConfig")
@patch("pathlib.Path.exists", return_value=True)
@patch("termux_dev_setup.otel.run_command")
def test_otel_service_start_success(mock_run, mock_exists, mock_config_class):
    with patch.object(OtelService, 'is_running', side_effect=[False, True]), \
         patch("termux_dev_setup.otel.success") as mock_success:
        service = OtelService()
        service.start()
        mock_success.assert_called_with("OpenTelemetry Collector started successfully.")

@patch("termux_dev_setup.otel.OtelConfig")
@patch("pathlib.Path.exists", return_value=True)
@patch("termux_dev_setup.otel.run_command")
@patch("time.sleep")
def test_otel_service_start_timeout(mock_sleep, mock_run, mock_exists, mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=False), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service = OtelService()
        service.start()
        mock_error.assert_called_with("OpenTelemetry Collector failed to start (timeout). Check logs.")

@patch("termux_dev_setup.otel.OtelConfig")
@patch("pathlib.Path.exists", return_value=True)
@patch("termux_dev_setup.otel.run_command", side_effect=Exception("Start failed"))
def test_otel_service_start_exception(mock_run, mock_exists, mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=False), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service = OtelService()
        service.start()
        assert "Failed to start OTEL" in mock_error.call_args[0][0]

@patch("termux_dev_setup.otel.OtelConfig")
def test_otel_service_stop_not_running(mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=False), \
         patch("termux_dev_setup.otel.success") as mock_success:
        service = OtelService()
        service.stop()
        mock_success.assert_called_with("OpenTelemetry Collector stopped.")

@patch("termux_dev_setup.otel.OtelConfig")
@patch("termux_dev_setup.otel.run_command")
@patch("time.sleep")
def test_otel_service_stop_success(mock_sleep, mock_run, mock_config_class):
    with patch.object(OtelService, 'is_running', side_effect=[True, False]), \
         patch("termux_dev_setup.otel.success") as mock_success:
        service = OtelService()
        service.stop()
        mock_success.assert_called_with("OpenTelemetry Collector stopped.")

@patch("termux_dev_setup.otel.OtelConfig")
@patch("termux_dev_setup.otel.run_command")
@patch("time.sleep")
def test_otel_service_stop_force_kill(mock_sleep, mock_run, mock_config_class):
    # is_running returns True for 10 loops, then True again (after force kill attempt), then False
    side_effect = [True] * 11 + [False]
    with patch.object(OtelService, 'is_running', side_effect=side_effect), \
         patch("termux_dev_setup.otel.success") as mock_success:
        service = OtelService()
        service.stop()
        mock_success.assert_called_with("OpenTelemetry Collector stopped (force kill).")

@patch("termux_dev_setup.otel.OtelConfig")
@patch("termux_dev_setup.otel.run_command")
@patch("time.sleep")
def test_otel_service_stop_force_kill_fail(mock_sleep, mock_run, mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=True), \
         patch("termux_dev_setup.otel.warning") as mock_warn:
        service = OtelService()
        service.stop()
        mock_warn.assert_called_with("Failed to stop OpenTelemetry Collector.")

@patch("termux_dev_setup.otel.OtelConfig")
@patch("termux_dev_setup.otel.run_command", side_effect=Exception("Stop failed"))
def test_otel_service_stop_exception(mock_run, mock_config_class):
    with patch.object(OtelService, 'is_running', return_value=True), \
         patch("termux_dev_setup.otel.error") as mock_error:
        service = OtelService()
        service.stop()
        assert "Error stopping OTEL" in mock_error.call_args[0][0]

@patch("termux_dev_setup.otel.OtelService")
def test_manage_otel(mock_service_class):
    mock_service = mock_service_class.return_value

    manage_otel("start")
    mock_service.start.assert_called_once()

    manage_otel("stop")
    mock_service.stop.assert_called_once()

    manage_otel("restart")
    mock_service.restart.assert_called_once()

    manage_otel("status")
    mock_service.status.assert_called_once()

@patch("socket.create_connection")
def test_is_port_open(mock_create_conn):
    assert otel.is_port_open(80) is True

    mock_create_conn.side_effect = Exception("Connection refused")
    assert otel.is_port_open(80) is False

def test_otel_service_restart():
    with patch.object(OtelService, 'stop') as mock_stop, \
         patch.object(OtelService, 'start') as mock_start, \
         patch("time.sleep"):
        service = OtelService()
        service.restart()
        mock_stop.assert_called_once()
        mock_start.assert_called_once()

def test_otel_service_status():
    with patch.object(OtelService, 'is_running', return_value=True), \
         patch("termux_dev_setup.otel.console.print") as mock_print:
        service = OtelService()
        service.status()
        assert any("UP" in str(arg) for call in mock_print.call_args_list for arg in call[0])

    with patch.object(OtelService, 'is_running', return_value=False), \
         patch("termux_dev_setup.otel.console.print") as mock_print:
        service = OtelService()
        service.status()
        assert any("DOWN" in str(arg) for call in mock_print.call_args_list for arg in call[0])
