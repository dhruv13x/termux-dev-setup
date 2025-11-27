from unittest.mock import patch, mock_open, call, MagicMock
import pytest
from termux_dev_setup import redis
from pathlib import Path

# =================== Fixtures ===================
@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch):
    """Auto-mock time.sleep to speed up tests."""
    monkeypatch.setattr(redis.time, 'sleep', MagicMock())

# =================== get_redis_password Tests ===================
@patch("builtins.open", new_callable=mock_open, read_data="requirepass mysecretpassword")
def test_get_redis_password_from_file(mock_file):
    mock_conf = MagicMock(spec=Path); mock_conf.exists.return_value = True
    assert redis.get_redis_password(mock_conf) == "mysecretpassword"

@patch("builtins.open", new_callable=mock_open, read_data="  requirepass   ")
def test_get_redis_password_empty_in_file(mock_file):
    mock_conf = MagicMock(spec=Path); mock_conf.exists.return_value = True
    assert redis.get_redis_password(mock_conf) == ""

@patch("builtins.open", side_effect=IOError("Permission denied"))
def test_get_redis_password_file_read_error(mock_file):
    mock_conf = MagicMock(spec=Path); mock_conf.exists.return_value = True
    assert redis.get_redis_password(mock_conf) == ""

def test_get_redis_password_from_env(monkeypatch):
    monkeypatch.setenv("REDIS_PASSWORD", "envsecret")
    assert redis.get_redis_password() == "envsecret"

# =================== manage_redis Tests ===================
@patch("termux_dev_setup.redis.is_port_open", return_value=True)
def test_manage_redis_start_already_running(mock_is_port_open):
    with patch("termux_dev_setup.redis.success") as mock_success:
        redis.manage_redis("start")
        mock_success.assert_called_with("Redis is already running on port 6379.")

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
@patch("pathlib.Path.exists", return_value=False)
def test_manage_redis_start_no_config(mock_exists, mock_is_port_open):
    with patch("termux_dev_setup.redis.error") as mock_error:
        redis.manage_redis("start")
        mock_error.assert_called_with(f"Config file {redis.DEFAULT_CONF} not found. Run 'tds setup redis' first.")

@patch("termux_dev_setup.redis.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command", return_value=True)
@patch("pathlib.Path.exists", return_value=True)
def test_manage_redis_start_success(mock_exists, mock_check, mock_run, mock_is_port_open):
    mock_run.return_value = MagicMock(returncode=0, stdout="PONG")
    redis.manage_redis("start")
    assert "runuser -u redis" in mock_run.call_args_list[0].args[0]
    assert "redis-cli" in mock_run.call_args_list[1].args[0]

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
@patch("termux_dev_setup.redis.run_command", side_effect=Exception("Launch failed"))
@patch("termux_dev_setup.redis.check_command", return_value=False)
@patch("pathlib.Path.exists", return_value=True)
def test_manage_redis_start_exception_with_su(mock_exists, mock_check, mock_run, mock_is_port_open):
    with patch("termux_dev_setup.redis.error") as mock_error:
        redis.manage_redis("start")
        assert "su - redis" in mock_run.call_args_list[0].args[0]
        mock_error.assert_called_with("Failed to start Redis: Launch failed")

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
@patch("termux_dev_setup.redis.run_command")
@patch("pathlib.Path.exists", return_value=True)
def test_manage_redis_start_timeout(mock_exists, mock_run, mock_is_port_open):
    mock_run.return_value = MagicMock(returncode=1, stdout="")
    with patch("termux_dev_setup.redis.error") as mock_error:
        redis.manage_redis("start")
        mock_error.assert_called_with("Redis failed to start (timeout).")

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
def test_manage_redis_stop_already_stopped(mock_is_port_open):
    with patch("termux_dev_setup.redis.success") as mock_success:
        redis.manage_redis("stop")
        mock_success.assert_called_with("Redis is already stopped.")

@patch("termux_dev_setup.redis.is_port_open", side_effect=[True, False])
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_stop_success(mock_run, mock_is_port_open):
    mock_run.return_value = MagicMock(returncode=0)
    redis.manage_redis("stop")
    mock_run.assert_called_once_with("redis-cli -p 6379 shutdown", shell=True, check=False, capture_output=True)

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_stop_force_kill(mock_run, mock_is_port_open):
    mock_run.side_effect = [MagicMock(returncode=1, stderr="Failed"), MagicMock()]
    with patch("termux_dev_setup.redis.warning") as mock_warning:
        redis.manage_redis("stop")
        mock_warning.assert_any_call("Shutdown failed: Failed")
        mock_run.assert_any_call("pkill redis-server", check=False)

@patch("termux_dev_setup.redis.is_port_open")
@patch("termux_dev_setup.redis.run_command")
@patch("pathlib.Path.exists", return_value=True) # THIS IS THE FIX
def test_manage_redis_restart(mock_path_exists, mock_run, mock_is_port_open):
    """Test the restart action calls stop and start correctly."""
    mock_is_port_open.side_effect = [True, False, False, True] # Stop, Start
    mock_run.side_effect = [
        MagicMock(returncode=0), # shutdown
        MagicMock(returncode=0), # redis-server
        MagicMock(returncode=0, stdout="PONG") # ping
    ]
    redis.manage_redis("restart")
    assert "shutdown" in mock_run.call_args_list[0].args[0]
    assert "redis-server" in mock_run.call_args_list[1].args[0]
    assert "ping" in mock_run.call_args_list[2].args[0]

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_status_healthy(mock_run, mock_is_port_open):
    mock_run.return_value = MagicMock(stdout="PONG")
    with patch("rich.console.Console.print") as mock_print:
        redis.manage_redis("status")
        mock_print.assert_any_call("  Health: [green]Healthy (PONG)[/green]")

# =================== setup_redis Tests ===================
@patch("termux_dev_setup.redis.manage_redis")
@patch("builtins.open", new_callable=mock_open)
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command", side_effect=[False, False, True]) # redis-server, id, adduser
def test_setup_redis_full_install(mock_check, mock_run, mock_file, mock_manage):
    redis.setup_redis()
    mock_run.assert_any_call("apt install -y redis-server")
    mock_run.assert_any_call("adduser --system --group --home '/var/lib/redis' redis", check=False)
    mock_file().write.assert_called()
    mock_manage.assert_called_with("start")

@patch("termux_dev_setup.redis.manage_redis")
@patch("termux_dev_setup.redis.run_command") # Mock away fs commands
@patch("builtins.open", new_callable=mock_open) # Mock away file write
@patch("termux_dev_setup.redis.check_command", side_effect=[True, False, False]) # redis-server, id, adduser
def test_setup_redis_no_adduser(mock_check, mock_open, mock_run, mock_manage):
    with patch("termux_dev_setup.redis.warning") as mock_warning:
        redis.setup_redis()
        mock_warning.assert_called_with("Could not create redis user (adduser not found).")

@patch("termux_dev_setup.redis.manage_redis")
@patch("builtins.open", side_effect=IOError("Can't write"))
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command", return_value=True)
def test_setup_redis_config_write_fails(mock_check, mock_run, mock_file, mock_manage):
    with patch("termux_dev_setup.redis.error") as mock_error:
        redis.setup_redis()
        mock_error.assert_called_with("Failed to write config file: Can't write")
