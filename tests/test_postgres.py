import pytest
import socket
from unittest.mock import patch, MagicMock, call
from termux_dev_setup import postgres
# Import from the new locations for patching
from termux_dev_setup.utils import postgres_utils, network
from termux_dev_setup.service_status import ServiceStatus
from pathlib import Path

# =================== Fixtures ===================
@pytest.fixture
def mock_pg_bin(monkeypatch):
    """Fixture to mock the get_pg_bin function to return a valid path."""
    mock_bin = MagicMock(spec=Path)
    mock_bin.__str__.return_value = "/usr/lib/postgresql/16/bin"
    mock_bin.parent.name = "16"

    def truediv_side_effect(arg):
        m = MagicMock()
        m.__str__.return_value = f"/usr/lib/postgresql/16/bin/{arg}"
        return m
    mock_bin.__truediv__.side_effect = truediv_side_effect

    monkeypatch.setattr(postgres, 'get_pg_bin', lambda: mock_bin)
    return mock_bin

@pytest.fixture
def mock_pg_bin_none(monkeypatch):
    """Fixture to mock get_pg_bin function to return None."""
    monkeypatch.setattr(postgres, 'get_pg_bin', lambda: None)

@pytest.fixture
def mock_view():
    """Fixture to mock PostgresView."""
    with patch("termux_dev_setup.postgres.PostgresView") as MockView:
        yield MockView.return_value

# =================== get_pg_bin Tests ===================
# These tests should now test the function in postgres_utils
def test_get_pg_bin_success():
    with patch("termux_dev_setup.utils.postgres_utils.Path") as mock_path:
        mock_pg_lib = MagicMock()
        mock_v14 = MagicMock(); mock_v14.name = "14"; mock_v14.is_dir.return_value = True
        mock_v16 = MagicMock(); mock_v16.name = "16"; mock_v16.is_dir.return_value = True
        mock_pg_lib.iterdir.return_value = [mock_v14, mock_v16]
        mock_path.return_value = mock_pg_lib
        assert postgres_utils.get_pg_bin() == mock_v16 / "bin"

def test_get_pg_bin_not_found():
    with patch("termux_dev_setup.utils.postgres_utils.Path") as mock_path:
        mock_pg_lib = MagicMock()
        mock_pg_lib.iterdir.return_value = []
        mock_path.return_value = mock_pg_lib
        assert postgres_utils.get_pg_bin() is None

def test_get_pg_bin_exception():
    with patch("termux_dev_setup.utils.postgres_utils.Path", side_effect=Exception("File error")):
        assert postgres_utils.get_pg_bin() is None

# =================== run_as_postgres / is_port_open Tests ===================
@patch("termux_dev_setup.utils.postgres_utils.run_command")
@patch("termux_dev_setup.utils.postgres_utils.check_command", return_value=True)
def test_run_as_postgres_with_runuser(mock_check, mock_run):
    """Test the primary path using 'runuser'."""
    postgres_utils.run_as_postgres("my_command")
    mock_check.assert_called_once_with("runuser")
    mock_run.assert_called_once_with('runuser -u postgres -- my_command', shell=True, check=True, capture_output=False)

@patch("termux_dev_setup.utils.postgres_utils.run_command")
@patch("termux_dev_setup.utils.postgres_utils.check_command", return_value=False)
def test_run_as_postgres_with_su(mock_check, mock_run):
    """Test the fallback to 'su' when 'runuser' is not present."""
    postgres_utils.run_as_postgres("my_command")
    mock_check.assert_called_once_with("runuser")
    mock_run.assert_called_once_with('su - postgres -c "my_command"', shell=True, check=True, capture_output=False)

@patch("socket.create_connection", side_effect=socket.error("Connection refused"))
def test_is_port_open_failure(mock_socket):
    """Test is_port_open when the connection fails."""
    assert not network.is_port_open()

def test_is_port_open_success():
    """Test is_port_open when the connection succeeds."""
    # We must patch socket.create_connection such that it doesn't raise exception
    # and context manager works.
    with patch("socket.create_connection", return_value=MagicMock()) as mock_socket:
        mock_socket.return_value.__enter__.return_value = None
        assert network.is_port_open()

# =================== manage_postgres Tests ===================
def test_manage_postgres_no_bin(mock_pg_bin_none, mock_view):
    """Test manage_postgres when pg_bin is not found."""
    postgres.manage_postgres("start")
    mock_view.print_error.assert_called_with("PostgreSQL binaries not found. Is it installed?")

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
def test_manage_postgres_start_already_running(mock_is_port_open, mock_pg_bin, mock_view):
    """Test starting postgres when it is already running."""
    postgres.manage_postgres("start")
    mock_view.print_success.assert_called_with("PostgreSQL is already running (port open).")

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.postgres.run_as_postgres")
def test_manage_postgres_start_success(mock_run_pg, mock_is_port_open, mock_pg_bin, mock_view):
    """Test successful start of postgres."""
    postgres.manage_postgres("start")
    mock_view.print_success.assert_called_with("PostgreSQL started successfully.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.time.sleep")
def test_manage_postgres_start_timeout(mock_sleep, mock_run_pg, mock_is_port_open, mock_pg_bin, mock_view):
    """Test start command timing out."""
    postgres.manage_postgres("start")
    mock_view.print_error.assert_called_with("PostgreSQL failed to start (timeout). Check logs.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
@patch("termux_dev_setup.postgres.run_as_postgres", side_effect=Exception("DB error"))
def test_manage_postgres_start_exception(mock_run_pg, mock_is_port_open, mock_pg_bin, mock_view):
    """Test an exception occurring during the start command."""
    postgres.manage_postgres("start")
    mock_view.print_error.assert_called_with("Failed to start PostgreSQL: DB error")

def test_manage_postgres_stop_no_bin(mock_pg_bin_none, mock_view):
    """Test stopping postgres when binaries are not found."""
    postgres.manage_postgres("stop")
    mock_view.print_error.assert_called_with("PostgreSQL binaries not found.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
def test_manage_postgres_stop_already_stopped(mock_is_port_open, mock_pg_bin, mock_view):
    """Test stopping postgres when it is already stopped."""
    postgres.manage_postgres("stop")
    mock_view.print_success.assert_called_with("PostgreSQL is already stopped.")

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[True, True, False])
@patch("termux_dev_setup.postgres.run_as_postgres")
def test_manage_postgres_stop_success(mock_run_pg, mock_is_port_open, mock_pg_bin, mock_view):
    """Test successful stop of postgres."""
    postgres.manage_postgres("stop")
    mock_view.print_success.assert_called_with("PostgreSQL stopped.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.time.sleep")
def test_manage_postgres_stop_timeout(mock_sleep, mock_run_pg, mock_is_port_open, mock_pg_bin, mock_view):
    """Test stop command timing out."""
    postgres.manage_postgres("stop")
    mock_view.print_warning.assert_called_with("Graceful stop failed or timed out.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
@patch("termux_dev_setup.postgres.run_as_postgres", side_effect=Exception("pg_ctl error"))
def test_manage_postgres_stop_exception(mock_run_pg, mock_is_port_open, mock_pg_bin, mock_view):
    """Test an exception occurring during the stop command."""
    postgres.manage_postgres("stop")
    mock_view.print_warning.assert_called_with("pg_ctl stop failed.")

@patch("termux_dev_setup.postgres.manage_postgres")
def test_manage_postgres_restart(mock_manage, mock_pg_bin):
    """Test restart command calls stop and start."""
    with patch("termux_dev_setup.postgres.time.sleep"):
        postgres.manage_postgres("restart")
        # manage_postgres calls Service.restart, which calls stop(), waits, then start().
        # Since we mocked manage_postgres, this test doesn't actually test the logic inside Service.restart properly.
        # We should test Service.restart directly or not mock manage_postgres.
        pass

@patch("termux_dev_setup.postgres.PostgresService")
def test_manage_postgres_restart_logic(MockService, mock_view):
    """Test restart logic calls stop then start."""
    service = MockService.return_value
    # Restart now returns ServiceResult
    service.stop.return_value = MagicMock(status=ServiceStatus.STOPPED, message="Stopped")
    service.start.return_value = MagicMock(status=ServiceStatus.RUNNING, message="Started")
    service.config.data_dir = "/data"

    postgres.manage_postgres("restart")
    # Updated expectation: manage_postgres calls stop() and start() manually now
    service.stop.assert_called_once()
    service.start.assert_called_once()

    mock_view.print_success.assert_any_call("Stopped")
    mock_view.print_success.assert_any_call("Started")

def test_postgres_service_restart(mock_pg_bin):
    service = postgres.PostgresService()
    # Mock stop and start to return valid ServiceResults
    with patch.object(service, 'stop') as mock_stop, \
         patch.object(service, 'start') as mock_start, \
         patch("termux_dev_setup.postgres.time.sleep"):

        mock_stop.return_value = MagicMock(status=ServiceStatus.STOPPED)
        mock_start.return_value = MagicMock(status=ServiceStatus.RUNNING)

        service.restart()
        mock_stop.assert_called_once()
        mock_start.assert_called_once()

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
def test_manage_postgres_status_down(mock_is_port_open, mock_pg_bin, mock_view):
    """Test postgres status command when service is down."""
    postgres.manage_postgres("status")
    mock_view.print_status.assert_called()

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
def test_manage_postgres_status_up(mock_is_port_open, mock_pg_bin, mock_view):
    """Test postgres status command when service is up."""
    postgres.manage_postgres("status")
    mock_view.print_status.assert_called()

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.postgres.run_as_postgres")
def test_manage_postgres_start_with_custom_env(mock_run_pg, mock_is_port_open, mock_pg_bin, monkeypatch, mock_view):
    """Test that start command respects PG_DATA and PG_LOG env vars."""
    custom_data = "/tmp/pgdata"
    custom_log = "/tmp/pg.log"
    monkeypatch.setenv("PG_DATA", custom_data)
    monkeypatch.setenv("PG_LOG", custom_log)
    postgres.manage_postgres("start")
    pg_ctl = mock_pg_bin / "pg_ctl"
    expected_cmd = f"'{pg_ctl}' -D '{custom_data}' -l '{custom_log}' start"
    mock_run_pg.assert_called_once_with(expected_cmd)

# Add explicit coverage tests for uncovered branches
def test_postgres_service_start_missing_binaries(mock_pg_bin_none):
    service = postgres.PostgresService()
    result = service.start()
    assert result.status == ServiceStatus.MISSING_BINARIES

def test_postgres_service_stop_missing_binaries(mock_pg_bin_none):
    service = postgres.PostgresService()
    result = service.stop()
    assert result.status == ServiceStatus.MISSING_BINARIES

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
def test_postgres_service_start_already_running(mock_is_port_open, mock_pg_bin):
    service = postgres.PostgresService()
    result = service.start()
    assert result.status == ServiceStatus.ALREADY_RUNNING

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
def test_postgres_service_stop_already_stopped(mock_is_port_open, mock_pg_bin):
    service = postgres.PostgresService()
    result = service.stop()
    assert result.status == ServiceStatus.ALREADY_STOPPED

# =================== setup_postgres Tests (Error/Edge Cases) ===================

@patch("termux_dev_setup.postgres.run_command", side_effect=[None, Exception("APT is broken")])
@patch("termux_dev_setup.postgres.check_command", return_value=True)
def test_setup_postgres_apt_install_fails(mock_check, mock_run, mock_view):
    """Test setup failure if 'apt install' fails."""
    postgres.setup_postgres()
    mock_view.print_error.assert_called_with("Failed to install postgresql packages via apt.")

@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
def test_setup_postgres_bin_detection_fails(mock_check, mock_run, mock_pg_bin_none, mock_view):
    """Test setup failure if bin directory isn't found after install."""
    postgres.setup_postgres()
    mock_view.print_error.assert_called_with("Failed to detect PostgreSQL installation after apt install.")

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", side_effect=[True, False, False, True]) # apt, id, adduser, useradd
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_with_useradd(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_is_port_open, mock_pg_bin):
    """Test user creation falls back to 'useradd'."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    postgres.setup_postgres()
    assert "useradd" in mock_run.call_args_list[2].args[0]

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", side_effect=[True, False, False, False]) # apt, id, adduser, useradd
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_no_user_creation_tool(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_is_port_open, mock_pg_bin, mock_view):
    """Test warning when no user creation tool is found."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    postgres.setup_postgres()
    mock_view.print_warning.assert_called_with("Could not create postgres user. Proceeding if user exists.")

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True]) # Need is_port_open to change for start()
@patch("termux_dev_setup.postgres.manage_postgres") # We are now using Controller, so this mock might not be hit if we call setup_postgres() which uses Controller.
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_db_already_initialized(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_is_port_open, mock_pg_bin):
    """Test the flow where the database is already initialized."""
    # Ensure install_packages returns True
    # Ensure get_pg_bin returns valid
    # Ensure ensure_user
    # Ensure init_db returns True early

    mock_path.return_value.__truediv__.return_value.exists.return_value = True # PG_VERSION exists

    # NOTE: setup_postgres() instantiates PostgresController.
    # PostgresController.setup() calls self.manage("start").
    # self.manage("start") calls self.service.start().
    # self.service.start() calls is_running().
    # We patched is_port_open to return False then True to simulate starting.

    postgres.setup_postgres()

    # Verify initdb was NOT called
    # initdb calls run_as_postgres(cmd) where cmd has 'initdb'
    assert not any("initdb" in str(c) for c in mock_run_pg.call_args_list)

@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres", side_effect=Exception("initdb failed"))
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_initdb_fails(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_pg_bin, mock_view):
    """Test setup flow when initdb command fails."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    postgres.setup_postgres()
    mock_view.print_error.assert_called_with("initdb failed.")

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_with_custom_user_env(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_is_port_open, mock_pg_bin, monkeypatch):
    """Test that setup respects PG_USER environment variable."""
    custom_user = "my_db_user"
    monkeypatch.setenv("PG_USER", custom_user)
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    postgres.setup_postgres()
    create_role_cmd = f"'{mock_pg_bin}/createuser' -s {custom_user}"
    assert any(create_role_cmd in str(c) for c in mock_run_pg.call_args_list)

@patch("termux_dev_setup.postgres.check_command", return_value=False)
def test_install_packages_no_apt(mock_check, mock_view):
    installer = postgres.PostgresInstaller(view=mock_view)
    assert installer.install_packages() is False
    mock_view.print_error.assert_called_with("apt not found. Ensure you are inside an Ubuntu/Debian proot-distro.")

def test_PostgresConfig_init(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "/custom/data")
    installer = postgres.PostgresInstaller()
    assert installer.config.data_dir == "/custom/data"

@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.run_command")
def test_ensure_user_calls_adduser(mock_run, mock_check):
    installer = postgres.PostgresInstaller()
    # Mock id postgres checks to fail first?
    # Logic: if not check_command("id postgres"):
    with patch("termux_dev_setup.postgres.check_command", side_effect=[False, True, False]): # id fail, adduser success
        installer.ensure_user()
        # Should call adduser
        assert any("adduser" in str(c) for c in mock_run.call_args_list)

def test_manage_postgres_controller_methods(mock_pg_bin, mock_view):
    """Coverage for controller methods."""
    controller = postgres.PostgresController()
    with patch.object(controller.service, 'is_running', return_value=True):
        controller.manage("status")
        mock_view.print_status.assert_called()

    with patch.object(controller.service, 'start', return_value=MagicMock(status=ServiceStatus.RUNNING)):
         controller.manage("start")
         mock_view.print_success.assert_called()

    with patch.object(controller.service, 'stop', return_value=MagicMock(status=ServiceStatus.STOPPED)):
         controller.manage("stop")
         mock_view.print_success.assert_called()
