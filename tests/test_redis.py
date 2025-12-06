from unittest.mock import patch, mock_open, call, MagicMock
import pytest
from termux_dev_setup import redis, config
from pathlib import Path
import os
import socket

# =================== Fixtures ===================
@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch):
    """Auto-mock time.sleep to speed up tests."""
    monkeypatch.setattr(redis.time, 'sleep', MagicMock())

# =================== RedisConfig Tests ===================
@patch("builtins.open", new_callable=mock_open, read_data="requirepass mysecretpassword")
def test_redis_config_from_file(mock_file):
    with patch("pathlib.Path.exists", return_value=True):
        c = config.RedisConfig()
        assert c.password == "mysecretpassword"

@patch("builtins.open", new_callable=mock_open, read_data="  requirepass   ")
def test_redis_config_empty_in_file(mock_file):
    with patch("pathlib.Path.exists", return_value=True):
        c = config.RedisConfig()
        assert c.password == ""

@patch("builtins.open", side_effect=IOError("Permission denied"))
def test_redis_config_file_read_error(mock_file):
    with patch("pathlib.Path.exists", return_value=True):
        c = config.RedisConfig()
        assert c.password == ""

def test_redis_config_from_env(monkeypatch):
    monkeypatch.setenv("REDIS_PASSWORD", "envsecret")
    c = config.RedisConfig()
    assert c.password == "envsecret"

# =================== manage_redis Tests ===================
@patch("termux_dev_setup.redis.is_port_open", return_value=True)
def test_manage_redis_start_already_running(mock_is_port_open):
    with patch("termux_dev_setup.redis.success") as mock_success:
        redis.manage_redis("start")
        mock_success.assert_called_with(f"Redis is already running on port 6379.")

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
@patch("pathlib.Path.exists", return_value=False)
def test_manage_redis_start_no_config(mock_exists, mock_is_port_open):
    with patch("termux_dev_setup.redis.error") as mock_error:
        redis.manage_redis("start")
        # Exact message depends on refactor, checking key phrases
        assert "Config file" in mock_error.call_args[0][0]
        assert "not found" in mock_error.call_args[0][0]

@patch("termux_dev_setup.redis.is_port_open", side_effect=[False, True])
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command", return_value=True)
@patch("pathlib.Path.exists", return_value=True)
def test_manage_redis_start_success(mock_exists, mock_check, mock_run, mock_is_port_open):
    # Mocking run_command results for ping loop
    # run_command called:
    # 1. start redis (shell=True) -> return MagicMock
    # 2. ping (capture_output=True) -> return MagicMock(returncode=0, stdout="PONG")

    # We use side_effect to return different mocks
    mock_run.side_effect = [
        MagicMock(returncode=0), # start
        MagicMock(returncode=0, stdout="PONG") # ping
    ]

    with patch("termux_dev_setup.redis.success") as mock_success:
        redis.manage_redis("start")
        mock_success.assert_called_with("Redis started successfully.")

    assert "runuser -u redis" in mock_run.call_args_list[0].args[0]

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
    # Mocking run_command: start ok, but pings fail
    mock_run.side_effect = [
        MagicMock(returncode=0), # start
    ] + [MagicMock(returncode=1, stdout="")] * 20 # pings fail

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
    assert "redis-cli" in mock_run.call_args_list[0].args[0]
    assert "shutdown" in mock_run.call_args_list[0].args[0]

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_stop_force_kill(mock_run, mock_is_port_open):
    mock_run.side_effect = [MagicMock(returncode=1, stderr="Failed"), MagicMock()]
    with patch("termux_dev_setup.redis.warning") as mock_warning:
        redis.manage_redis("stop")
        mock_warning.assert_any_call("Shutdown failed: Failed")
        mock_run.assert_any_call("pkill redis-server", check=False)

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_stop_exception(mock_run, mock_is_port_open):
    mock_run.side_effect = Exception("Stop error")
    with patch("termux_dev_setup.redis.error") as mock_error:
        redis.manage_redis("stop")
        mock_error.assert_called_with("Error stopping Redis: Stop error")

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command", return_value=MagicMock(returncode=0))
def test_manage_redis_stop_graceful_failed(mock_run, mock_is_port_open):
    # Always running
    with patch("termux_dev_setup.redis.warning") as mock_warning:
        redis.manage_redis("stop")
        mock_warning.assert_called_with("Graceful stop failed.")

@patch("termux_dev_setup.redis.is_port_open")
@patch("termux_dev_setup.redis.run_command")
@patch("pathlib.Path.exists", return_value=True)
def test_manage_redis_restart(mock_path_exists, mock_run, mock_is_port_open):
    """Test the restart action calls stop and start correctly."""
    # stop calls is_port_open -> True
    # then waits, is_port_open -> False (stopped)
    # start calls is_port_open -> False (stopped)
    # then waits, is_port_open -> True (started) [Wait, start doesn't check is_running in loop, it checks ping]

    mock_is_port_open.side_effect = [True, False, False]

    # Run command sequence:
    # 1. shutdown (stop)
    # 2. start command (start)
    # 3. ping command (start check)

    mock_run.side_effect = [
        MagicMock(returncode=0), # shutdown
        MagicMock(returncode=0), # redis-server start
        MagicMock(returncode=0, stdout="PONG") # ping
    ]

    redis.manage_redis("restart")

    # Verify calls exist
    assert any("shutdown" in str(args) for args, kwargs in mock_run.call_args_list)
    assert any("redis-server" in str(args) for args, kwargs in mock_run.call_args_list)

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_status_healthy(mock_run, mock_is_port_open):
    mock_run.return_value = MagicMock(stdout="PONG")
    with patch("rich.console.Console.print") as mock_print:
        redis.manage_redis("status")
        # Check if one of the calls contains Healthy
        assert any("Healthy (PONG)" in str(args) for args, kwargs in mock_print.call_args_list)

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command")
def test_manage_redis_status_unresponsive(mock_run, mock_is_port_open):
    mock_run.return_value = MagicMock(stdout="")
    with patch("rich.console.Console.print") as mock_print:
        redis.manage_redis("status")
        assert any("Unresponsive" in str(args) for args, kwargs in mock_print.call_args_list)

@patch("termux_dev_setup.redis.is_port_open", return_value=True)
@patch("termux_dev_setup.redis.run_command", side_effect=Exception("Ping fail"))
def test_manage_redis_status_check_failed(mock_run, mock_is_port_open):
    with patch("rich.console.Console.print") as mock_print:
        redis.manage_redis("status")
        assert any("Check Failed" in str(args) for args, kwargs in mock_print.call_args_list)

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
def test_manage_redis_status_down(mock_is_port_open):
    with patch("rich.console.Console.print") as mock_print:
        redis.manage_redis("status")
        assert any("DOWN" in str(args) for args, kwargs in mock_print.call_args_list)

@patch("termux_dev_setup.redis.is_port_open", return_value=False)
def test_is_port_open_failure(mock_is_port_open):
    assert redis.is_port_open() is False

def test_is_port_open_socket_exception():
    with patch("socket.create_connection", side_effect=Exception("Conn err")):
        assert redis.is_port_open() is False

# =================== setup_redis Tests ===================
@patch("termux_dev_setup.redis.manage_redis")
@patch("builtins.open", new_callable=mock_open)
@patch("termux_dev_setup.redis.run_command")
@patch("termux_dev_setup.redis.check_command", side_effect=[False, False, True]) # redis-server, id, adduser
def test_setup_redis_full_install(mock_check, mock_run, mock_file, mock_manage):
    redis.setup_redis()
    # Check for apt install
    assert any("apt install -y redis-server" in str(args) for args, kwargs in mock_run.call_args_list)
    # Check for adduser
    assert any("adduser" in str(args) for args, kwargs in mock_run.call_args_list)
    # Check for setup_directories (mkdir/chown)
    assert any("mkdir" in str(args) for args, kwargs in mock_run.call_args_list)
    # Check config write
    mock_file().write.assert_called()
    # Check manage start
    mock_manage.assert_called_with("start")

def test_setup_redis_with_version():
    with patch("termux_dev_setup.redis.run_command") as mock_run, \
         patch("termux_dev_setup.redis.check_command", return_value=True), \
         patch("termux_dev_setup.redis.manage_redis"), \
         patch("termux_dev_setup.redis.info") as mock_info, \
         patch("builtins.open", mock_open()) as mock_file:

        version = "6.0"
        redis.setup_redis(version=version)

        # Verify that we logged the version request
        mock_info.assert_any_call(f"Requested Redis version: {version}")

@patch("termux_dev_setup.redis.manage_redis")
@patch("termux_dev_setup.redis.run_command")
@patch("builtins.open", new_callable=mock_open)
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

@patch("termux_dev_setup.redis.check_command", return_value=False)
@patch("termux_dev_setup.redis.run_command", side_effect=[None, Exception("Install fail")])
def test_install_packages_fail(mock_run, mock_check):
    installer = redis.RedisInstaller()
    with patch("termux_dev_setup.redis.error") as mock_error:
        assert installer.install_packages() is False
        mock_error.assert_called_with("Failed to install redis-server via apt.")

@patch("termux_dev_setup.redis.run_command")
@patch("builtins.open", new_callable=mock_open)
@patch("termux_dev_setup.redis.Path")
def test_generate_config_backup(mock_path_cls, mock_file, mock_run):
    # Mock Path instances
    mock_conf = MagicMock()
    mock_conf.exists.return_value = True

    mock_orig = MagicMock()
    mock_orig.exists.return_value = False

    def path_side_effect(arg):
        # RedisInstaller uses self.config.conf_path for conf_path
        # And f"{conf_path}.orig" for orig path

        # If arg ends with .orig, return mock_orig
        if str(arg).endswith(".orig"):
            return mock_orig

        # We assume any other path creation is for the config file or directories,
        # but for this test we mainly care about conf_path
        return mock_conf

    mock_path_cls.side_effect = path_side_effect

    installer = redis.RedisInstaller()
    installer.generate_config()

    assert any("cp" in str(args) and ".orig" in str(args) for args, kwargs in mock_run.call_args_list)
