import pytest
import socket
from unittest.mock import patch, MagicMock, call
from termux_dev_setup import postgres
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

# =================== get_pg_bin Tests ===================
def test_get_pg_bin_success():
    with patch("termux_dev_setup.postgres.Path") as mock_path:
        mock_pg_lib = MagicMock()
        mock_v14 = MagicMock(); mock_v14.name = "14"; mock_v14.is_dir.return_value = True
        mock_v16 = MagicMock(); mock_v16.name = "16"; mock_v16.is_dir.return_value = True
        mock_pg_lib.iterdir.return_value = [mock_v14, mock_v16]
        mock_path.return_value = mock_pg_lib
        assert postgres.get_pg_bin() == mock_v16 / "bin"

def test_get_pg_bin_not_found():
    with patch("termux_dev_setup.postgres.Path") as mock_path:
        mock_pg_lib = MagicMock()
        mock_pg_lib.iterdir.return_value = []
        mock_path.return_value = mock_pg_lib
        assert postgres.get_pg_bin() is None

def test_get_pg_bin_exception():
    with patch("termux_dev_setup.postgres.Path", side_effect=Exception("File error")):
        assert postgres.get_pg_bin() is None

# =================== run_as_postgres / is_port_open Tests ===================
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
def test_run_as_postgres_with_runuser(mock_check, mock_run):
    """Test the primary path using 'runuser'."""
    postgres.run_as_postgres("my_command")
    mock_check.assert_called_once_with("runuser")
    mock_run.assert_called_once_with('runuser -u postgres -- my_command', shell=True, check=True, capture_output=False)

@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=False)
def test_run_as_postgres_with_su(mock_check, mock_run):
    """Test the fallback to 'su' when 'runuser' is not present."""
    postgres.run_as_postgres("my_command")
    mock_check.assert_called_once_with("runuser")
    mock_run.assert_called_once_with('su - postgres -c "my_command"', shell=True, check=True, capture_output=False)

@patch("socket.create_connection", side_effect=socket.error("Connection refused"))
def test_is_port_open_failure(mock_socket):
    """Test is_port_open when the connection fails."""
    assert not postgres.is_port_open()

# =================== manage_postgres Tests ===================
def test_manage_postgres_no_bin(mock_pg_bin_none):
    """Test manage_postgres when pg_bin is not found."""
    with patch("termux_dev_setup.postgres.error") as mock_error:
        postgres.manage_postgres("start")
        mock_error.assert_called_with("PostgreSQL binaries not found. Is it installed?")

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
@patch("termux_dev_setup.postgres.run_as_postgres", side_effect=Exception("DB error"))
def test_manage_postgres_start_exception(mock_run_pg, mock_is_port_open, mock_pg_bin):
    """Test an exception occurring during the start command."""
    with patch("termux_dev_setup.postgres.error") as mock_error:
        postgres.manage_postgres("start")
        mock_error.assert_called_with("Failed to start PostgreSQL: DB error")

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.time.sleep")
def test_manage_postgres_stop_timeout(mock_sleep, mock_run_pg, mock_is_port_open, mock_pg_bin):
    """Test stop command timing out."""
    with patch("termux_dev_setup.postgres.warning") as mock_warning:
        postgres.manage_postgres("stop")
        mock_warning.assert_called_with("Graceful stop failed or timed out.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=True)
@patch("termux_dev_setup.postgres.run_as_postgres", side_effect=Exception("pg_ctl error"))
def test_manage_postgres_stop_exception(mock_run_pg, mock_is_port_open, mock_pg_bin):
    """Test an exception occurring during the stop command."""
    with patch("termux_dev_setup.postgres.warning") as mock_warning:
        postgres.manage_postgres("stop")
        mock_warning.assert_called_with("pg_ctl stop failed.")

@patch("termux_dev_setup.postgres.is_port_open", return_value=False)
@patch("rich.console.Console.print")
def test_manage_postgres_status_down(mock_print, mock_is_port_open, mock_pg_bin):
    """Test postgres status command when service is down."""
    postgres.manage_postgres("status")
    mock_print.assert_any_call("  Status: [bold red]DOWN[/bold red]")

@patch("termux_dev_setup.postgres.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.postgres.run_as_postgres")
def test_manage_postgres_start_with_custom_env(mock_run_pg, mock_is_port_open, mock_pg_bin, monkeypatch):
    """Test that start command respects PG_DATA and PG_LOG env vars."""
    custom_data = "/tmp/pgdata"
    custom_log = "/tmp/pg.log"
    monkeypatch.setenv("PG_DATA", custom_data)
    monkeypatch.setenv("PG_LOG", custom_log)
    postgres.manage_postgres("start")
    pg_ctl = mock_pg_bin / "pg_ctl"
    expected_cmd = f"'{pg_ctl}' -D '{custom_data}' -l '{custom_log}' start"
    mock_run_pg.assert_called_once_with(expected_cmd)


# =================== setup_postgres Tests (Error/Edge Cases) ===================

@patch("termux_dev_setup.postgres.run_command", side_effect=[None, Exception("APT is broken")])
@patch("termux_dev_setup.postgres.check_command", return_value=True)
def test_setup_postgres_apt_install_fails(mock_check, mock_run):
    """Test setup failure if 'apt install' fails."""
    with patch("termux_dev_setup.postgres.error") as mock_error:
        postgres.setup_postgres()
        mock_error.assert_called_with("Failed to install PostgreSQL packages via apt.")

@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
def test_setup_postgres_bin_detection_fails(mock_check, mock_run, mock_pg_bin_none):
    """Test setup failure if bin directory isn't found after install."""
    with patch("termux_dev_setup.postgres.error") as mock_error:
        postgres.setup_postgres()
        mock_error.assert_called_with("Failed to detect PostgreSQL installation after apt install.")

@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", side_effect=[True, False, False, True]) # apt, id, adduser, useradd
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_with_useradd(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_pg_bin):
    """Test user creation falls back to 'useradd'."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    postgres.setup_postgres()
    assert "useradd" in mock_run.call_args_list[2].args[0]

@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", side_effect=[True, False, False, False]) # apt, id, adduser, useradd
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_no_user_creation_tool(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_pg_bin):
    """Test warning when no user creation tool is found."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    with patch("termux_dev_setup.postgres.warning") as mock_warning:
        postgres.setup_postgres()
        mock_warning.assert_called_with("Could not create postgres user. Proceeding if user exists.")

@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_db_already_initialized(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_pg_bin):
    """Test the flow where the database is already initialized."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = True # PG_VERSION exists
    postgres.setup_postgres()
    assert not any("initdb" in str(c) for c in mock_run_pg.call_args_list)

@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres", side_effect=Exception("initdb failed"))
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_initdb_fails(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_pg_bin):
    """Test setup flow when initdb command fails."""
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    with patch("termux_dev_setup.postgres.error") as mock_error:
        postgres.setup_postgres()
        mock_error.assert_called_with("initdb failed.")

@patch("termux_dev_setup.postgres.manage_postgres")
@patch("termux_dev_setup.postgres.run_as_postgres")
@patch("termux_dev_setup.postgres.run_command")
@patch("termux_dev_setup.postgres.check_command", return_value=True)
@patch("termux_dev_setup.postgres.Path")
def test_setup_postgres_with_custom_user_env(mock_path, mock_check, mock_run, mock_run_pg, mock_manage, mock_pg_bin, monkeypatch):
    """Test that setup respects PG_USER environment variable."""
    custom_user = "my_db_user"
    monkeypatch.setenv("PG_USER", custom_user)
    mock_path.return_value.__truediv__.return_value.exists.return_value = False
    postgres.setup_postgres()
    create_role_cmd = f"'{mock_pg_bin}/createuser' -s {custom_user}"
    assert any(create_role_cmd in str(c) for c in mock_run_pg.call_args_list)
